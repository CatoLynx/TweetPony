# Copyright (C) 2013 Julian Metzler
# See the LICENSE file for the full license.

class APIError(Exception):
	def __init__(self, code, description, body = None):
		self.code = code
		self.description = description
		self.body = body
	
	def __str__(self):
		return "#%i: %s" % (self.code, self.description)

class ParameterError(Exception):
	def __init__(self, description):
		self.description = description
	
	def __str__(self):
		return self.description