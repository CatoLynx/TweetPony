# Copyright (C) 2013 Julian Metzler
# See the LICENSE file for the full license.

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
		print "Hello, @%s! You have been authenticated. You can now run the other eample scripts without having to authenticate every time." % api.user.screen_name

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