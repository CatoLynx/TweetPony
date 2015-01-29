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