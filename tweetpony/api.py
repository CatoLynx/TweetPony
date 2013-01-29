# Copyright (C) 2013 Julian Metzler
# See the LICENSE file for the full license.

import base64
import binascii
import hashlib
import hmac
import json
import random
import requests
import time
import urllib
import urlparse
from threading import Thread

from endpoints import *
from models import *

class APIError(Exception):
	def __init__(self, code, description):
		self.code = code
		self.description = description
	
	def __str__(self):
		return "#%i: %s" % (self.code, self.description)

class ParameterError(Exception):
	def __init__(self, description):
		self.description = description
	
	def __str__(self):
		return self.description

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

class API:
	def __init__(self, consumer_key, consumer_secret, access_token = None, access_token_secret = None, host = "api.twitter.com", root = "/1.1/", oauth_host = "api.twitter.com", oauth_root = "/oauth/", secure = True):
		self.consumer_key = consumer_key
		self.consumer_secret = consumer_secret
		self.access_token = access_token
		self.access_token_secret = access_token_secret
		self.host = host
		self.root = root
		self.oauth_host = oauth_host
		self.oauth_root = oauth_root
		self.secure = secure
		self._endpoint = None
		self._multipart = False
		self.user = self.verify_credentials() if self.access_token and self.access_token_secret else None
	
	def __getattr__(self, attr):
		self._endpoint = attr
		return self.api_call
	
	def parse_qs(self, qs):
		return dict([(key, values[0]) for key, values in urlparse.parse_qs(qs).iteritems()])
	
	def oauth_generate_nonce(self):
		return base64.b64encode(hashlib.sha1(str(random.getrandbits(256))).digest(), random.choice(['rA','aZ','gQ','hH','hG','aR','DD'])).rstrip('==')
	
	def get_oauth_header_data(self):
		auth_data = {
			'oauth_consumer_key': self.consumer_key,
			'oauth_nonce': self.oauth_generate_nonce(),
			'oauth_signature_method': "HMAC-SHA1",
			'oauth_timestamp': str(int(time.time())),
			'oauth_version': "1.0",
		}
		if self.access_token:
			auth_data['oauth_token'] = self.access_token
		return auth_data
	
	def generate_oauth_header(self, auth_data):
		return {'Authorization': "OAuth %s" % ", ".join(['%s="%s"' % item for item in auth_data.items()])}
	
	def get_oauth_header(self, method, url, get = None, post = None):
		if not self._multipart:
			get_data = (get or {}).items()
			post_data = (post or {}).items()
		else:
			get_data = []
			post_data = []
		auth_data = self.get_oauth_header_data().items()
		data = [(urllib.quote(key, safe = "~"), urllib.quote(value, safe = "~")) for key, value in get_data + post_data + auth_data]
		data = sorted(sorted(data), key = lambda item: item[0].upper())
		param_string = []
		for key, value in data:
			param_string.append("%s=%s" % (key, value))
		param_string = "&".join(param_string)
		signature_base = []
		signature_base.append(method.upper())
		signature_base.append(urllib.quote(url, safe = "~"))
		signature_base.append(urllib.quote(param_string, safe = "~"))
		signature_base = "&".join(signature_base)
		token_secret = urllib.quote(self.access_token_secret, safe = "~") if self.access_token_secret else ""
		signing_key = "&".join([urllib.quote(self.consumer_secret, safe = "~"), token_secret])
		signature = hmac.new(signing_key, signature_base, hashlib.sha1)
		signature = urllib.quote(binascii.b2a_base64(signature.digest())[:-1], safe = "~")
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
	
	def do_request(self, method, url, get = None, post = None, files = None, stream = False, is_json = True):
		if files == {}:
			files = None
		self._multipart = files is not None
		header = self.get_oauth_header(method, url, get, post)
		if get:
			full_url = url + "?" + urllib.urlencode(get)
		else:
			full_url = url
		if method.upper() == "POST":
			response = requests.post(full_url, data = post, files = files, headers = header, stream = stream)
		else:
			response = requests.get(full_url, data = post, files = files, headers = header, stream = stream)
		if response.status_code != 200:
			try:
				data = response.json()
				raise APIError(code = data['errors'][0]['code'], description = data['errors'][0]['message'])
			except APIError:
				raise
			except:
				raise APIError(code = response.status_code, description = " ".join(response.headers['status'].split()[1:]))
		if stream:
			return response
		if is_json:
			try:
				return response.json()
			except:
				return response.text
		else:
			return response.text
	
	def request_token(self):
		url = self.build_request_url(self.oauth_root, 'request_token')
		resp = self.do_request("GET", url, is_json = False)
		token_data = self.parse_qs(resp)
		self.access_token = token_data['oauth_token']
		self.access_token_secret = token_data['oauth_token_secret']
		return (self.access_token, self.access_token_secret)
	
	def get_auth_url(self, token = None):
		if token is None:
			token, secret = self.request_token()
		return self.build_request_url(self.oauth_root, 'authenticate', {'oauth_token': token})
	
	def authenticate(self, verifier):
		url = self.build_request_url(self.oauth_root, 'access_token')
		resp = self.do_request("GET", url, is_json = False)
		token_data = self.parse_qs(resp)
		self.access_token = token_data['oauth_token']
		self.access_token_secret = token_data['oauth_token_secret']
		self.user = self.verify_credentials()
		return ((self.access_token, self.access_token_secret), token_data['user_id'], token_data['screen_name'])
	
	def parse_param(self, key, value):
		if type(value) == bool:
			value = "true" if value else "false"
		return (key, value)
	
	def parse_params(self, params):
		files = {}
		_params = dict(params.items())
		for key, value in params.iteritems():
			if value is None:
				del _params[key]
			if key == 'image' or key == 'media' or key == 'banner':
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
			p = kwargs.get(param) or files.get(param)
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
		
		if stream:
			url = self.build_request_url(self.root, endpoint, host = data['host'])
		else:
			url = self.build_request_url(self.root, endpoint)
		
		resp = self.do_request("POST" if data['post'] else "GET", url, get_data, post_data, files, stream = stream)
		if stream:
			for line in resp.iter_lines():
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
