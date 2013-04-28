#!/usr/bin/env python
# Copyright (C) 2013 Julian Metzler
# See the LICENSE file for the full license.

"""
This script authenticates the user and asks for something to tweet.
"""

import tweetpony

def main():
	try:
		api = tweetpony.API(tweetpony.CONSUMER_KEY, tweetpony.CONSUMER_SECRET)
		url = api.get_auth_url()
		print "Visit this URL to obtain your verification code: %s" % url
		verifier = raw_input("Input your code: ")
		api.authenticate(verifier)
	except tweetpony.APIError as err:
		print "Oh no! You could not be authenticated. Twitter returned error #%i and said: %s" % (err.code, err.description)
	tweet = raw_input("Hello, %s! Compose a tweet: " % api.user.screen_name)
	try:
		status = api.update_status(status = tweet)
	except tweetpony.APIError as err:
		print "Oh no! Your tweet could not be sent. Twitter returned error #%i and said: %s" % (err.code, err.description)
	else:
		print "Yay! Your tweet has been sent! View it here: https://twitter.com/%s/status/%s" % (status.user.screen_name, status.id_str)

if __name__ == "__main__":
	main()