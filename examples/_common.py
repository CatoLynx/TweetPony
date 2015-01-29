# Copyright 2013 Julian Metzler

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

"""
This file contains functions used by more than one example script.
"""

import json
import os
import tweetpony

def authenticate():
	try:
		api = tweetpony.API(tweetpony.CONSUMER_KEY, tweetpony.CONSUMER_SECRET)
		url = api.get_auth_url()
		print "Visit this URL to obtain your verification code: %s" % url
		verifier = raw_input("Input your code: ")
		api.authenticate(verifier)
	except tweetpony.APIError as err:
		print "Oh no! You could not be authenticated. Twitter returned error #%i and said: %s" % (err.code, err.description)
	else:
		auth_data = {'access_token': api.access_token, 'access_token_secret': api.access_token_secret}
		with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".auth_data.json"), 'w') as f:
			f.write(json.dumps(auth_data))
		print "Hello, @%s! You have been authenticated. You can now run the other example scripts without having to authenticate every time." % api.user.screen_name

def get_api():
	if not os.path.exists(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".auth_data.json")):
		authenticate()
	with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".auth_data.json"), 'r') as f:
		auth_data = json.loads(f.read())
	try:
		api = tweetpony.API(tweetpony.CONSUMER_KEY, tweetpony.CONSUMER_SECRET, auth_data['access_token'], auth_data['access_token_secret'])
	except tweetpony.APIError as err:
		print "Oh no! You could not be authenticated. Twitter returned error #%i and said: %s" % (err.code, err.description)
	else:
		return api
	return False