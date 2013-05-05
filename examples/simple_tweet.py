#!/usr/bin/env python
# Copyright (C) 2013 Julian Metzler
# See the LICENSE file for the full license.

"""
This script asks for something to tweet.
"""

from _common import get_api
import tweetpony

def main():
	api = get_api()
	if not api:
		return
	tweet = raw_input("Hello, %s! Compose a tweet: " % api.user.screen_name)
	try:
		status = api.update_status(status = tweet)
	except tweetpony.APIError as err:
		print "Oh no! Your tweet could not be sent. Twitter returned error #%i and said: %s" % (err.code, err.description)
	else:
		print "Yay! Your tweet has been sent! View it here: https://twitter.com/%s/status/%s" % (status.user.screen_name, status.id_str)

if __name__ == "__main__":
	main()