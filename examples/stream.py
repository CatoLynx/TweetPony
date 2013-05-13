#!/usr/bin/env python
# Copyright (C) 2013 Julian Metzler
# See the LICENSE file for the full license.

"""
This script starts a user stream and displays new tweets.
"""

from _common import get_api
import tweetpony

class StreamProcessor(tweetpony.StreamProcessor):
	def on_status(self, status):
		print "%s: %s" % (status.user.screen_name, status.text)
		return True

def main():
	api = get_api()
	if not api:
		return
	processor = StreamProcessor(api)
	try:
		api.user_stream(processor = processor)
	except KeyboardInterrupt:
		pass

if __name__ == "__main__":
	main()