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

import base64
import binascii
import hashlib
import hmac
import json
import random
try:
	import requests
except ImportError:
	raise ImportError("It seems like you don't have the 'requests' module installed which is required for TweetPony to work. Please install it first.")
import time
import urllib
import urlparse
from threading import Thread

from endpoints import *
from error import *
from models import *
from utils import quote

class ArgList(tuple):
	def __getitem__(self, index):
		if index > len(self) - 1:
			return None
		else:
			return tuple.__getitem__(self, index)

class KWArgDict(dict):
	def __getitem__(self, key):
		if key not in self.keys():
			return None
		else:
			return dict.__getitem__(self, key)

class API(object):
	def __init__(self, consumer_key, consumer_secret, access_token = None, access_token_secret = None, host = "api.twitter.com", root = "/1.1/", oauth_host = "api.twitter.com", oauth_root = "/oauth/", secure = True, timeout = None, load_user = True, json_in_models = False):
		self.consumer_key = consumer_key
		self.consumer_secret = consumer_secret
		self.access_token = access_token
		self.access_token_secret = access_token_secret
		self.host = host
		self.root = root
		self.oauth_host = oauth_host
		self.oauth_root = oauth_root
		self.secure = secure
		self.timeout = timeout
		self.load_user = load_user
		self._endpoint = None
		self._multipart = False
		self.json_in_models = json_in_models
		self.request_token = None
		self.request_token_secret = None
		self.user = self.verify_credentials() if self.load_user and self.access_token and self.access_token_secret else DummyUser()
	
	def __getattr__(self, attr):
		if attr.startswith("__"):
			return object.__getattr__(self, attr)
		self._endpoint = attr
		return self.api_call
	
	def set_access_token(self, access_token, access_token_secret):
		self.access_token = access_token
		self.access_token_secret = access_token_secret
		if self.load_user:
			self.verify()
	
	def verify(self):
		self.user = self.verify_credentials()
	
	def set_request_token(self, request_token, request_token_secret):
		self.request_token = request_token
		self.request_token_secret = request_token_secret
	
	def parse_qs(self, qs):
		return dict([(key, values[0]) for key, values in urlparse.parse_qs(qs).iteritems()])
	
	def oauth_generate_nonce(self):
		return base64.b64encode(hashlib.sha1(str(random.getrandbits(256))).digest(), random.choice(['rA','aZ','gQ','hH','hG','aR','DD'])).rstrip('==')
	
	def get_oauth_header_data(self, callback_url = None):
		auth_data = {
			'oauth_consumer_key': self.consumer_key,
			'oauth_nonce': self.oauth_generate_nonce(),
			'oauth_signature_method': "HMAC-SHA1",
			'oauth_timestamp': str(int(time.time())),
			'oauth_version': "1.0",
		}
		if callback_url:
			auth_data['oauth_callback'] = callback_url
		if self.access_token:
			auth_data['oauth_token'] = self.access_token
		elif self.request_token:
			auth_data['oauth_token'] = self.request_token
		return auth_data
	
	def generate_oauth_header(self, auth_data):
		return {'Authorization': "OAuth %s" % ", ".join(['%s="%s"' % item for item in auth_data.items()])}
	
	def get_oauth_header(self, method, url, callback_url = None, get = None, post = None):
		if not self._multipart:
			get_data = (get or {}).items()
			post_data = (post or {}).items()
		else:
			get_data = []
			post_data = []
		auth_data = self.get_oauth_header_data(callback_url = callback_url).items()
		data = [(quote(key, safe = "~"), quote(value, safe = "~")) for key, value in get_data + post_data + auth_data]
		data = sorted(sorted(data), key = lambda item: item[0].upper())
		param_string = []
		for key, value in data:
			param_string.append("%s=%s" % (key, value))
		param_string = "&".join(param_string)
		signature_base = []
		signature_base.append(method.upper())
		signature_base.append(quote(url, safe = "~"))
		signature_base.append(quote(param_string, safe = "~"))
		signature_base = "&".join(signature_base)
		if self.request_token:
			token_secret = quote(self.request_token_secret, safe = "~")
		elif self.access_token:
			token_secret = quote(self.access_token_secret, safe = "~")
		else:
			token_secret = ""
		signing_key = "&".join([quote(self.consumer_secret, safe = "~"), token_secret])
		signature = hmac.new(signing_key, signature_base, hashlib.sha1)
		signature = quote(binascii.b2a_base64(signature.digest())[:-1], safe = "~")
		auth_data.append(('oauth_signature', signature))
		return self.generate_oauth_header(dict(auth_data))
	
	def build_request_url(self, root, endpoint, get_data = None, host = None):
		host = host or self.host
		scheme = "https" if self.secure else "http"
		url = "%s://%s%s%s" % (scheme, host, root, endpoint)
		if get_data:
			qs = urllib.urlencode(get_data)
			url += "?%s" % qs
		return url
	
	def do_request(self, method, url, callback_url = None, get = None, post = None, files = None, stream = False, is_json = True):
		if files == {}:
			files = None
		self._multipart = files is not None
		header = self.get_oauth_header(method, url, callback_url, get, post)
		if get:
			full_url = url + "?" + urllib.urlencode(get)
		else:
			full_url = url
		"""# DEBUG
		info = "=" * 50 + "\n"
		info += "Method:    %s\n" % method
		info += "URL:       %s\n" % full_url
		info += "Headers:   %s\n" % str(header)
		info += "GET data:  %s\n" % str(get)
		info += "POST data: %s\n" % str(post)
		info += "Files:     %s\n" % str(files)
		info += "Streaming: %s\n" % str(stream)
		info += "JSON:      %s\n" % str(is_json)
		info += "=" * 50
		print info
		# END DEBUG"""
		if method.upper() == "POST":
			response = requests.post(full_url, data = post, files = files, headers = header, stream = stream, timeout = self.timeout)
		else:
			response = requests.get(full_url, data = post, files = files, headers = header, stream = stream, timeout = self.timeout)
		"""# DEBUG
		print ("\nResponse:  %s\n" % response.text) + "=" * 50
		# END DEBUG"""
		if response.status_code != 200:
			try:
				data = response.json()
				try:
					raise APIError(code = data['errors'][0]['code'], description = data['errors'][0]['message'], body = response.text or None)
				except TypeError:
					raise APIError(code = None, description = data['errors'])
			except APIError:
				raise
			except:
				description = " ".join(response.headers['status'].split()[1:]) if response.headers.get('status', None) else "Unknown Error"
				raise APIError(code = response.status_code, description = description, body = response.text or None)
		if stream:
			return response
		if is_json:
			try:
				return response.json()
			except:
				return response.text
		else:
			return response.text
	
	def get_request_token(self, callback_url = None):
		url = self.build_request_url(self.oauth_root, 'request_token')
		resp = self.do_request("POST", url, callback_url, is_json = False)
		token_data = self.parse_qs(resp)
		self.set_request_token(token_data['oauth_token'], token_data['oauth_token_secret'])
		return (self.request_token, self.request_token_secret, token_data.get('oauth_callback_confirmed'))
	
	def get_auth_url(self, callback_url = None, force_login = False, screen_name = None, token = None):
		self.set_request_token(None, None)
		if token is None:
			token, secret, callback_confirmed = self.get_request_token(callback_url)
		if callback_url and not callback_confirmed:
			raise APIError(code = None, description = "OAuth callback not confirmed")
		data = {'oauth_token': token}
		if force_login:
			data['force_login'] = 'true'
		if screen_name:
			data['screen_name'] = screen_name
		return self.build_request_url(self.oauth_root, 'authenticate', data)
	
	def authenticate(self, verifier):
		url = self.build_request_url(self.oauth_root, 'access_token')
		resp = self.do_request("POST", url, post = {'oauth_verifier': verifier}, is_json = False)
		token_data = self.parse_qs(resp)
		self.set_request_token(None, None)
		self.set_access_token(token_data['oauth_token'], token_data['oauth_token_secret'])
		return ((self.access_token, self.access_token_secret), token_data['user_id'], token_data['screen_name'])
	
	def parse_param(self, key, value):
		if key == 'media':
			# This only comes in here when we're uploading multiple images, so ignore it
			return (key, value)
		
		if type(value) == bool:
			value = "true" if value else "false"
		elif type(value) in (tuple, list):
			value = ",".join([str(val) for val in value])
		elif type(value) not in (str, unicode) and value is not None:
			value = unicode(value)
		return (key, value)
	
	def parse_params(self, params):
		files = {}
		_params = dict(params.items())
		for key, value in params.iteritems():
			if value in [None, []]:
				del _params[key]
			if key in ['image', 'media', 'banner']:
				multiple_media = False
				if type(value) is file:
					try:
						value.seek(0)
					except ValueError:
						pass
				elif type(value) in (str, unicode):
					value = open(value, 'rb')
				elif type(value) in (list, tuple):
					# Used when uploading multiple images
					multiple_media = True
					value = list(value)
					for index, item in enumerate(value):
						if type(item) is file:
							try:
								item.seek(0)
							except ValueError:
								pass
						elif type(item) in (str, unicode):
							value[index] = open(item, 'rb')
					_params[key] = value
				
				if not multiple_media:
					del _params[key]
					if key == 'media':
						key = 'media[]'
					files[key] = value
		params = _params
		parsed_params = dict([self.parse_param(key, value) for key, value in params.iteritems()])
		return (parsed_params, files)
	
	def parse_stream_entity(self, entity):
		try:
			data = json.loads(entity)
		except ValueError:
			return None
		keys = data.keys()
		if 'delete' in keys:
			instance = DeletionEvent.from_json(data['delete'])
		elif 'scrub_geo' in keys:
			instance = LocationDeletionEvent.from_json(data['scrub_geo'])
		elif 'limit' in keys:
			instance = LimitEvent.from_json(data['limit'])
		elif 'status_withheld' in keys:
			instance = WithheldStatusEvent.from_json(data['status_withheld'])
		elif 'user_withheld' in keys:
			instance = WithheldUserEvent.from_json(data['user_withheld'])
		elif 'disconnect' in keys:
			instance = DisconnectEvent.from_json(data['disconnect'])
		elif 'friends' in keys:
			instance = IDCollection.from_json(data['friends'])
		elif 'target' in keys:
			instance = Event.from_json(data)
		elif 'direct_message' in keys:
			instance = Message.from_json(data['direct_message'])
		else:
			instance = Status.from_json(data)
		return instance
	
	def api_call(self, *args, **kwargs):
		if self._endpoint not in ENDPOINTS and self._endpoint not in STREAM_ENDPOINTS:
			raise NotImplementedError("API endpoint for method '%s' not found." % self._endpoint)
		
		stream = self._endpoint in STREAM_ENDPOINTS
		if stream:
			endpoints = STREAM_ENDPOINTS
			processor = kwargs.get('processor', StreamProcessor(self))
			if 'processor' in kwargs.keys():
				del kwargs['processor']
		else:
			endpoints = ENDPOINTS
		
		args = ArgList(args)
		kwargs, files = self.parse_params(kwargs)
		kwargs = KWArgDict(kwargs)
		data = endpoints[self._endpoint]
		
		if args:
			keys = data['url_params'] + data['required_params'] + data['optional_params']
			additional_kwargs, additional_files = self.parse_params(dict(zip(keys, args)))
			used_keys = additional_kwargs.keys()
			used_file_keys = additional_files.keys()
			duplicate_keys = [key for key in used_keys if key in kwargs]
			duplicate_file_keys = [key for key in used_file_keys if key in files]
			
			if duplicate_keys or duplicate_file_keys:
				raise ParameterError("Duplicate values for parameters: %s" % ", ".join(duplicate_keys + duplicate_file_keys))
			
			kwargs.update(additional_kwargs)
			files.update(additional_files)

		missing_params = []
		url_params = []
		for param in data['url_params']:
			p = kwargs.get(param)
			if p is None:
				missing_params.append(param)
			else:
				url_params.append(p)
				del kwargs[param]
		if missing_params:
			raise ParameterError("Missing URL parameters: %s" % ", ".join(missing_params))
		
		missing_params = []
		for param in data['required_params']:
			p = files.get(param) or kwargs.get(param)
			if p is None:
				missing_params.append(param)
		if missing_params:
			raise ParameterError("Missing required parameters: %s" % ", ".join(missing_params))
		
		unsupported_params = []
		for param in kwargs.keys():
			if param not in data['url_params'] + data['required_params'] + data['optional_params']:
				unsupported_params.append(param)
		for param in files.keys():
			if param not in data['url_params'] + data['required_params'] + data['optional_params']:
				unsupported_params.append(param)
		if unsupported_params:
			raise ParameterError("Unsupported parameters specified: %s" % ", ".join(unsupported_params))
		
		if self._endpoint == 'update_status_with_media':
			# This is a 2-step process and different from the rest of the API calls, so we need to handle it differently
			# First we upload all the media files and gather the assigned IDs
			ids = []
			for media in kwargs['media']:
				url = self.build_request_url(self.root, "media/upload.json", host = "upload.twitter.com")
				resp = self.do_request("POST", url, files = {'media': media})
				ids.append(resp['media_id'])
			
			# Now we have our IDs and can continue with a normal status update, except we pass the additional id list parameter
			del kwargs['media']
			kwargs['media_ids'] = self.parse_param('media_ids', ids)[1]
		
		if data['url_params'] != []:
			endpoint = data['endpoint'] % tuple(url_params)
		else:
			endpoint = data['endpoint']
		
		if data['post']:
			get_data = None
			post_data = kwargs
		else:
			get_data = kwargs
			post_data = None
		
		if 'host' in data:
			url = self.build_request_url(self.root, endpoint, host = data['host'])
		else:
			url = self.build_request_url(self.root, endpoint)
		
		resp = self.do_request("POST" if data['post'] else "GET", url, get = get_data, post = post_data, files = files, stream = stream)
		if stream:
			for line in resp.iter_lines(chunk_size = 1):
				if not line:
					continue
				entity = self.parse_stream_entity(line)
				entity.connect_api(self)
				if processor.process_entity(entity) == False:
					break
		else:
			if data['model'] is None:
				return resp
			else:
				model = data['model'].from_json(resp)
				model.connect_api(self)
				return model

class StreamProcessor:
	def __init__(self, api):
		self.api = api
	
	def process_entity(self, entity):
		t = type(entity)
		if t == Status:
			return self.on_status(entity)
		elif t == Message:
			return self.on_message(entity)
		elif t == Event:
			return self.on_event(entity)
		elif t == DeletionEvent:
			return self.on_delete(entity)
		elif t == LocationDeletionEvent:
			return self.on_geo_delete(entity)
		elif t == LimitEvent:
			return self.on_limit(entity)
		elif t == WithheldStatusEvent:
			return self.on_withheld_status(entity)
		elif t == WithheldUserEvent:
			return self.on_withheld_user(entity)
		elif t == DisconnectEvent:
			return self.on_disconnect(entity)
		elif t == IDCollection:
			return self.on_friends(entity)
		else:
			return self.on_unknown_entity(entity)
		return True
	
	def on_status(self, status):
		return True
	
	def on_message(self, message):
		return True
	
	def on_event(self, event):
		return True
	
	def on_delete(self, event):
		return True
	
	def on_geo_delete(self, event):
		return True
	
	def on_limit(self, event):
		return True
	
	def on_withheld_status(self, event):
		return True
	
	def on_withheld_user(self, event):
		return True
	
	def on_disconnect(self, event):
		return True
	
	def on_friends(self, friends):
		return True
	
	def on_unknown_entity(self, entity):
		return True

class BufferedStreamProcessor(StreamProcessor):
	def __init__(self, api, max_items = 25):
		StreamProcessor.__init__(self, api)
		self.buffer = []
		self.max_items = max_items
		self.source_running = True
		self.buffer_running = True
		self.buffer_processor = Thread(target = self.process_buffer)
		self.buffer_processor.start()
	
	def process_entity(self, entity):
		if not self.source_running:
			while self.buffer_running:
				time.sleep(0.1)
			return False
		if not self.max_items or (self.max_items and len(self.buffer) < self.max_items):
			self.buffer.append(entity)
		elif self.max_items and len(self.buffer) >= self.max_items:
			self.source_running = False
		return True
	
	def process_buffer(self):
		while self.buffer_running:
			if not self.buffer:
				if self.source_running:
					time.sleep(0.1)
				else:
					self.buffer_running = False
				continue
			entity = self.buffer.pop(0)
			result = StreamProcessor.process_entity(self, entity)
			if not result:
				self.source_running = False
			time.sleep(1)

if __name__ == '__main__':
	print "Rainbow Dash ist best pony! :3"
