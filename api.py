# Copyright (C) 2013 Julian Metzler
# See the LICENSE file for the full license.

import base64
import binascii
import hashlib
import hmac
import json
import random
import time
import urllib
import urllib2
import urlparse
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
from endpoints import *

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
		self.user = self.verify_credentials()
	
	def __getattr__(self, attr):
		self._endpoint = attr
		return self.api_call
	
	def parse_qs(self, qs):
		return dict([(key, values[0]) for key, values in urlparse.parse_qs(qs).iteritems()])
	
	def oauth_generate_nonce(self):
		return base64.b64encode(hashlib.sha1(str(random.getrandbits(256))).digest(), random.choice(['rA','aZ','gQ','hH','hG','aR','DD'])).rstrip('==')
	
	def oauth_authorize_request(self, request):
		auth_data = {
			'oauth_consumer_key': self.consumer_key,
			'oauth_nonce': self.oauth_generate_nonce(),
			'oauth_signature_method': "HMAC-SHA1",
			'oauth_timestamp': str(int(time.time())),
			'oauth_version': "1.0",
			'oauth_token': self.access_token,
		}
		request.add_header('Authorization', "OAuth %s" % ",".join(['%s="%s"' % item for item in auth_data.items()]))
		return request
	
	def oauth_sign_request(self, request):
		method = request.get_method()
		scheme, host, path, params, query, fragment = urlparse.urlparse(request.get_full_url())
		base_url = "%s://%s%s" % (scheme, host, path)
		if not self._multipart:
			get_data = self.parse_qs(query).items()
			post_data = (self.parse_qs(request.get_data() or "")).items()
		else:
			get_data = []
			post_data = []
		auth_data = {}
		auth_header = request.get_header('Authorization')
		if auth_header.startswith("OAuth"):
			auth_data_raw = [item.strip() for item in " ".join(auth_header.split()[1:]).split(",")]
			for item in auth_data_raw:
				key, value = item.split("=")
				auth_data[key] = value.replace('"', "")
		auth_data = auth_data.items()
		data = [(urllib.quote(key, safe = "~"), urllib.quote(value, safe = "~")) for key, value in get_data + post_data + auth_data]
		data = sorted(sorted(data), key = lambda item: item[0].upper())
		param_string = []
		for key, value in data:
			param_string.append("%s=%s" % (key, value))
		param_string = "&".join(param_string)
		signature_base = []
		signature_base.append(method.upper())
		signature_base.append(urllib.quote(base_url, safe = "~"))
		signature_base.append(urllib.quote(param_string, safe = "~"))
		signature_base = "&".join(signature_base)
		token_secret = urllib.quote(self.access_token_secret, safe = "~") if self.access_token_secret else ""
		signing_key = "&".join([urllib.quote(self.consumer_secret, safe = "~"), token_secret])
		signature = hmac.new(signing_key, signature_base, hashlib.sha1)
		signature = urllib.quote(binascii.b2a_base64(signature.digest())[:-1], safe = "~")
		auth_data.append(('oauth_signature', signature))
		request.add_header('Authorization', "OAuth %s" % ", ".join(['%s="%s"' % item for item in auth_data]))
		return request
	
	def build_request_url(self, root, endpoint, get_data = None):
		scheme = "https" if self.secure else "http"
		url = "%s://%s%s%s" % (scheme, self.host, root, endpoint)
		if get_data:
			qs = urllib.urlencode(get_data)
			url += "?%s" % qs
		return url
	
	def do_request(self, request, is_json = True):
		request = self.oauth_authorize_request(request)
		request = self.oauth_sign_request(request)
		try:
			response = urllib2.urlopen(request)
		except urllib2.HTTPError as err:
			try:
				data = json.loads(err.read())
				raise APIError(code = data['errors'][0]['code'], description = data['errors'][0]['message'])
			except APIError:
				raise
			except:
				raise APIError(code = err.code, description = err.reason)
		rdata = response.read()
		if is_json:
			if len(rdata) == 0:
				return None
			else:
				try:
					return json.loads(rdata)
				except ValueError:
					return rdata
		else:
			return rdata
	
	def request_token(self):
		url = self.build_request_url(self.oauth_root, 'request_token')
		req = urllib2.Request(url, data = "")
		resp = self.do_request(req, is_json = False)
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
		req = urllib2.Request(url, data = urllib.urlencode({'oauth_verifier': verifier}))
		resp = self.do_request(req, is_json = False)
		token_data = self.parse_qs(resp)
		self.access_token = token_data['oauth_token']
		self.access_token_secret = token_data['oauth_token_secret']
		return ((self.access_token, self.access_token_secret), token_data['user_id'], token_data['screen_name'])
	
	def parse_param(self, key, value):
		if type(value) == bool:
			value = "true" if value else "false"
		if key == 'image' or key == 'media' or key == 'banner':
			self._multipart = True
		if key == 'media':
			key = 'media[]'
		return (key, value)
	
	def parse_params(self, params):
		_params = dict(params.items())
		for key, value in params.iteritems():
			if value is None:
				del _params[key]
		params = _params
		parsed_params = dict([self.parse_param(key, value) for key, value in params.iteritems()])
		return parsed_params
	
	def api_call(self, *args, **kwargs):
		if self._endpoint not in ENDPOINTS:
			raise NotImplementedError("API endpoint for method '%s' not found." % self._endpoint)
		
		self._multipart = False
		args = ArgList(args)
		kwargs = KWArgDict(self.parse_params(kwargs))
		data = ENDPOINTS[self._endpoint]
		
		missing_params = []
		url_params = []
		for param in data['url_params']:
			p = kwargs.get(param)
			if p is None:
				missing_params.append(param)
			else:
				url_params.append(p)
				del kwargs[param]
		if missing_params != []:
			raise ParameterError("Missing URL parameters: %s" % ", ".join(missing_params))
		
		missing_params = []
		for param in data['required_params']:
			p = kwargs.get(param)
			if p is None:
				missing_params.append(param)
		if missing_params != []:
			raise ParameterError("Missing required parameters: %s" % ", ".join(missing_params))
		
		unsupported_params = []
		for param in kwargs.keys():
			if param not in data['url_params'] + data['required_params'] + data['optional_params']:
				unsupported_params.append(param)
		if unsupported_params != []:
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
		
		url = self.build_request_url(self.root, endpoint, get_data)
		req = urllib2.Request(url)
		
		if self._multipart:
			register_openers()
			post_data, headers = multipart_encode(post_data)
			for key, value in headers.iteritems():
				req.add_header(key, value)
		else:
			post_data = urllib.urlencode(post_data) if post_data else "" if data['post'] else None
		
		req.add_data(post_data)
		resp = self.do_request(req)
		if resp is None:
			return resp
		if data['model'] is None:
			return resp
		else:
			model = data['model'].from_json(resp)
			model.connect_api(self)
			return model

if __name__ == '__main__':
	print "Rainbow Dash ist best pony! :3"
