# Copyright 2013-2015 Julian Metzler

"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import json
import locale
import utils

from datetime import datetime
from error import ParameterError

def strptime(string, fmt = '%a %b %d %H:%M:%S +0000 %Y'):
	locale.setlocale(locale.LC_TIME, 'C')
	value = datetime.strptime(string, fmt)
	locale.setlocale(locale.LC_TIME, '')
	return value

class DummyAPI:
	def __getattr__(self, name):
		raise NotImplementedError("This model does not have an API instance associated with it.")

class DummyUser:
	def __getattr__(self, name):
		raise NotImplementedError("This API instance does not have verified credentials and thus did not load the authenticating user's profile.")

class AttrDict(dict):
	def __init__(self, data = None):
		if data is not None:
			for key, value in data.iteritems():
				if type(value) == dict:
					value = AttrDict(value)
				elif type(value) == list:
					for i in range(len(value)):
						if type(value[i]) == dict:
							value[i] = AttrDict(value[i])
						elif type(value[i]) == list:
							for n in range(len(value[i])):
								if type(value[i][n]) == dict:
									value[i][n] = AttrDict(value[i][n])
				self[key] = value
	
	def __getattr__(self, name):
		try:
			return self.__getitem__(name)
		except KeyError:
			raise AttributeError

class Model(AttrDict):
	api = DummyAPI()
	
	def __getattr__(self, name):
		try:
			return self.__getitem__(name)
		except:
			return AttrDict.__getattr__(self, name)
	
	@classmethod
	def from_json(cls, data):
		self = cls(data)
		self['json'] = json.dumps(data)
		return self
	
	def connect_api(self, api):
		self.api = api
		if not api.json_in_models:
			del self['json']

class ModelCollection(list):
	model = Model
	
	@classmethod
	def from_json(cls, data):
		self = cls()
		for item in data:
			self.append(self.model.from_json(item))
		return self
	
	def connect_api(self, api):
		for item in self:
			if hasattr(item, 'connect_api'):
				item.connect_api(api)
	
	def __iter__(self):
		self._iterator = list.__iter__(self)
		return self._iterator
	
	def next(self):
		return self._iterator.next()

class MixedModelCollection(Model):
	model_key = 'models'
	collection = ModelCollection
	
	@classmethod
	def from_json(cls, data):
		if type(data) is list and len(data) == 1:
			data = data[0]
		self = cls(Model.from_json(data))
		for key, value in self.iteritems():
			if key == self.model_key:
				value = self.collection.from_json(value)
			self[key] = value
		return self
	
	def connect_api(self, api):
		for item in self.get(self.model_key, []):
			if hasattr(item, 'connect_api'):
				item.connect_api(api)

	def __len__(self):
		return len(self.get(self.model_key, []))

	def __getitem__(self, descriptor):
		if type(descriptor) in [str, unicode]:
			return Model.__getitem__(self, descriptor)
		else:
			return self.get(self.model_key, []).__getitem__(descriptor)
	
	def __iter__(self):
		return self.get(self.model_key, []).__iter__()
	
	def next(self):
		return self.get(self.model_key, []).next()

class CursoredModelCollection(MixedModelCollection):
	pass

########################################################

class Status(Model):
	@classmethod
	def from_json(cls, data):
		self = cls(Model.from_json(data))
		tmp = cls()
		for key, value in self.iteritems():
			if key == 'created_at':
				value = strptime(value)
			elif key == 'user':
				value = User.from_json(value)
			elif key == 'text':
				value = value.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
			elif key == 'retweeted_status':
				value = Status.from_json(value)
			elif key == 'source':
				try:
					tmp[u'source_url'] = value.split('"')[1]
					value = value.split(">")[1].split("<")[0]
				except IndexError:
					tmp[u'source_url'] = None
			tmp[key] = value
		self = tmp
		return self
	
	def clean_text(self):
		return self.text
	
	def favorite(self):
		return self.api.favorite(id = self.id)
	
	def unfavorite(self):
		return self.api.unfavorite(id = self.id)
	
	def retweet(self):
		return self.api.retweet(id = self.id)
	
	def delete(self):
		return self.api.delete_status(id = self.id)
	
	def reply(self, text, reply_all = False, **kwargs):
		if reply_all:
			text = utils.optimize_mentions([self.user.screen_name] + [entity.screen_name for entity in self.entities.user_mentions], text)
		else:
			text = utils.optimize_mentions([self.user.screen_name], text)
		return self.api.update_status(status = text, in_reply_to_status_id = self.id, **kwargs)
	
	def retweets(self, **kwargs):
		return self.api.retweets(id = self.id, **kwargs)

class User(Model):
	@classmethod
	def from_json(cls, data):
		self = cls(Model.from_json(data))
		for key, value in self.iteritems():
			if key == 'created_at':
				value = strptime(value)
			elif key == 'status':
				value = Status.from_json(value)
			self[key] = value
		return self
	
	def follow(self, **kwargs):
		return self.api.follow(user_id = self.id, **kwargs)
	
	def unfollow(self):
		return self.api.unfollow(user_id = self.id)
	
	def mention(self, text, **kwargs):
		text = utils.optimize_mentions([self.screen_name], text)
		return self.api.update_status(status = text, **kwargs)
	
	def add_to_list(self, list_id = None, slug = None, owner_screen_name = None, owner_id = None):
		if (list_id is None and slug is None) or (list_id is None and owner_screen_name is None and owner_id is None):
			raise ParameterError("You must specify either a list ID or a slug in combination with either the owner's screen name or their user ID.")
		return self.api.add_to_list(user_id = self.id, list_id = list_id, slug = slug, owner_screen_name = owner_screen_name, owner_id = owner_id)
	
	def remove_from_list(self, list_id = None, slug = None, owner_screen_name = None, owner_id = None):
		if (list_id is None and slug is None) or (list_id is None and owner_screen_name is None and owner_id is None):
			raise ParameterError("You must specify either a list ID or a slug in combination with either the owner's screen name or their user ID.")
		return self.api.remove_from_list(user_id = self.id, list_id = list_id, slug = slug, owner_screen_name = owner_screen_name, owner_id = owner_id)
	
	def block(self):
		return self.api.block(user_id = self.id)
	
	def unblock(self):
		return self.api.unblock(user_id = self.id)
	
	def report_spam(self):
		return self.api.report_spam(user_id = self.id)
	
	def send_message(self, text):
		return self.api.send_message(user_id = self.id, text = text)
	
	def friendship(self, target_id = None, target_screen_name = None):
		if target_id is None and target_screen_name is None:
			target_id = self.api.user.id
		return self.api.get_friendship(source_id = self.id, target_id = target_id, target_screen_name = target_screen_name)
	
	def followers(self, **kwargs):
		return self.api.followers(user_id = self.id, **kwargs)
	
	def friends(self, **kwargs):
		return self.api.friends(user_id = self.id, **kwargs)
	
	def followers_ids(self, **kwargs):
		return self.api.followers_ids(user_id = self.id, **kwargs)
	
	def friends_ids(self, **kwargs):
		return self.api.friends_ids(user_id = self.id, **kwargs)
	
	def lists(self):
		return self.api.lists(user_id = self.id)
	
	def list_memberships(self):
		return self.api.list_memberships(user_id = self.id)
	
	def favorites(self):
		return self.api.favorites(user_id = self.id)

class Message(Model):
	@classmethod
	def from_json(cls, data):
		self = cls(Model.from_json(data))
		for key, value in self.iteritems():
			if key == 'created_at':
				value = strptime(value)
			elif key == 'sender' or key == 'recipient':
				value = User.from_json(value)
			self[key] = value
		return self
	
	def delete(self):
		return self.api.delete_message(id = self.id)
	
	def reply(self, text):
		return self.api.send_message(user_id = self.sender.id, text = text)

class OEmbed(Model):
	pass

class Relationship(Model):
	@classmethod
	def from_json(cls, data):
		self = cls(Model.from_json(data['relationship']))
		self['following'] = self['source']['following']
		self['followed_by'] = self['source']['followed_by']
		return self

class SimpleRelationship(Model):
	@classmethod
	def from_json(cls, data):
		self = cls(Model.from_json(data))
		tmp = cls()
		for key, value in self.iteritems():
			if key == 'connections':
				tmp['followed_by'] = 'followed_by' in value
				tmp['following'] = 'following' in value
				tmp['following_requested'] = 'following_requested' in value
			tmp[key] = value
		self = tmp
		return self

class Settings(Model):
	pass

class Sizes(Model):
	pass

class List(Model):
	@classmethod
	def from_json(cls, data):
		self = cls(Model.from_json(data))
		for key, value in self.iteritems():
			if key == 'created_at':
				value = strptime(value)
			elif key == 'user':
				value = User.from_json(value)
			self[key] = value
		return self
	
	def delete(self):
		return self.api.delete_list(list_id = self.id)
	
	def update(self, name = None, mode = None, description = None):
		return self.api.update_list(list_id = self.id, name = name, mode = mode, description = description)
	
	def add_user(self, user_id = None, screen_name = None):
		return self.api.add_to_list(list_id = self.id, user_id = user_id, screen_name = screen_name)
	
	def remove_user(self, user_id = None, screen_name = None):
		return self.api.remove_from_list(list_id = self.id, user_id = user_id, screen_name = screen_name)
	
	def add_users(self, user_id = None, screen_name = None):
		return self.api.batch_add_to_list(list_id = self.id, user_id = user_id, screen_name = screen_name)
	
	def remove_users(self, user_id = None, screen_name = None):
		return self.api.batch_remove_from_list(list_id = self.id, user_id = user_id, screen_name = screen_name)

class SavedSearch(Model):
	@classmethod
	def from_json(cls, data):
		self = cls(Model.from_json(data))
		for key, value in self.iteritems():
			if key == 'created_at':
				value = strptime(value)
			self[key] = value
		return self
	
	def results(self, **kwargs):
		return self.api.search_tweets(q = self.query, **kwargs)
	
	def delete(self):
		return self.api.delete_saved_search(id = self.id)

class Place(Model):
	@classmethod
	def from_json(cls, data):
		self = cls(Model.from_json(data))
		for key, value in self.iteritems():
			if key == 'contained_within':
				value = [Place.from_json(item) for item in value]
			self[key] = value
		return self
	
	def similar(self, lat, long, **kwargs):
		return self.api.similar_places(lat = lat, long = long, name = self.name, **kwargs)

class PlaceSearchResult(Model):
	@classmethod
	def from_json(cls, data):
		self = cls(Model.from_json(data))
		for key, value in self.iteritems():
			if key == 'result':
				value['places'] = PlaceCollection.from_json(value['places'])
			self[key] = value
		return self

class Trend(Model):
	pass

class TrendLocation(Model):
	pass

class APIConfiguration(Model):
	pass

class Language(Model):
	pass

class RateLimitStatus(Model):
	pass

class Event(Model):
	@classmethod
	def from_json(cls, data):
		self = cls(Model.from_json(data))
		for key, value in self.iteritems():
			if key == 'target' or key == 'source':
				value = User.from_json(value)
			self[key] = value
		if 'favorite' in self['event']:
			self['target_object'] = Status.from_json(self['target_object'])
		elif self['event'].startswith('list_'):
			self['target_object'] = List.from_json(self['target_object'])
		return self

class DeletionEvent(Model):
	pass

class LocationDeletionEvent(Model):
	pass

class LimitEvent(Model):
	pass

class WithheldStatusEvent(Model):
	pass

class WithheldUserEvent(Model):
	pass

class DisconnectEvent(Model):
	pass

class PrivacyPolicy(str):
	@classmethod
	def from_json(cls, data):
		self = cls(data['privacy'].encode('utf-8'))
		return self
	
	def connect_api(self, api):
		pass

class TermsOfService(str):
	@classmethod
	def from_json(cls, data):
		self = cls(data['tos'].encode('utf-8'))
		return self
	
	def connect_api(self, api):
		pass

class StatusCollection(ModelCollection):
	model = Status

class UserCollection(ModelCollection):
	model = User

class MessageCollection(ModelCollection):
	model = Message

class IDCollection(list):
	@classmethod
	def from_json(cls, data):
		self = cls(data)
		return self
	
	def connect_api(self, api):
		pass

class RelationshipCollection(ModelCollection):
	model = Relationship

class SimpleRelationshipCollection(ModelCollection):
	model = SimpleRelationship

class ListCollection(ModelCollection):
	model = List

class SavedSearchCollection(ModelCollection):
	model = SavedSearch

class PlaceCollection(ModelCollection):
	model = Place

class TrendCollection(ModelCollection):
	model = Trend

class TrendLocationCollection(ModelCollection):
	model = TrendLocation

class LanguageCollection(ModelCollection):
	model = Language

class SearchResult(MixedModelCollection):
	model_key = 'statuses'
	collection = StatusCollection

class Category(MixedModelCollection):
	model_key = 'users'
	collection = UserCollection

class Trends(MixedModelCollection):
	model_key = 'trends'
	collection = TrendCollection

class CursoredIDCollection(CursoredModelCollection):
	model_key = 'ids'
	collection = IDCollection

class CursoredUserCollection(CursoredModelCollection):
	model_key = 'users'
	collection = UserCollection

class CursoredListCollection(CursoredModelCollection):
	model_key = 'lists'
	collection = ListCollection

class CategoryCollection(ModelCollection):
	model = Category
