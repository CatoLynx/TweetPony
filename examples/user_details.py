#!/usr/bin/env python
# Copyright (C) 2013 Julian Metzler
# See the LICENSE file for the full license.

"""
This script asks for a username and displays that user's profile data.
"""

from _common import get_api
import tweetpony

def main():
	api = get_api()
	if not api:
		return
	username = raw_input("Username to lookup (leave blank for your own): ").strip()
	if username == "":
		username = api.user.screen_name
	try:
		user = api.get_user(screen_name = username)
	except tweetpony.APIError as err:
		print "Oh no! The user's profile could not be loaded. Twitter returned error #%i and said: %s" % (err.code, err.description)
	else:
		for key, value in user.iteritems():
			if key in ['entities', 'json', 'status']:
				continue
			line = "%s " % key.replace("_", " ").capitalize()
			line += "." * (50 - len(line)) + " "
			line += unicode(value)
			print line

if __name__ == "__main__":
	main()