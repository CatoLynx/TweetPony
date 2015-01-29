#!/usr/bin/env python
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