#!/usr/bin/env python
# Copyright (C) 2013 Julian Metzler
# See the LICENSE file for the full license.

"""
This script fetches the current trending topics locations and displays the trends for the location the user selected.
"""

from _common import get_api
import tweetpony

def main():
	api = get_api()
	if not api:
		return
	try:
		locations = api.trend_locations()
	except tweetpony.APIError as err:
		print "Could not fetch the trend locations. Twitter returned error #%i and said: %s" % (err.code, err.description)
		return
	for location in locations:
		if location.placeType.code in [12, 19]: # Country (12) or Worldwide (19)
			print "%(woeid)i %(name)s" % location
		else: # Town (7) or other place type
			print "%(woeid)i %(name)s, %(country)s" % location
	selected_id = raw_input("Enter the number of the region you want to see the trends for: ")
	try:
		selected_trends = api.trends(id = selected_id)
	except tweetpony.APIError as err:
		print "Could not fetch the trends. Twitter returned error #%i and said: %s" % (err.code, err.description)
	else:
		print "\nHere are the trends!"
		print "=" * 25
		for trend in selected_trends:
			print trend.name

if __name__ == "__main__":
	main()