# Copyright (C) 2013 Julian Metzler
# See the LICENSE file for the full license.

import re
from urllib import quote as _quote

def optimize_mentions(usernames, text):
	username = re.compile(r'(?:^|[^\w]+)(?P<name>@\w+)')
	existing_mentions = username.findall(text.lower())
	missing_mentions = [name for name in usernames if name.lower() not in existing_mentions]
	text = "%s %s" % (" ".join(["@%s" % name for name in missing_mentions]), text)
	return text

def quote(text, *args, **kwargs):
	t = type(text)
	if t is str:
		converted_text = text
	elif t is unicode:
		converted_text = str(text.encode('utf-8'))
	else:
		try:
			converted_text = str(text)
		except:
			converted_text = text
	return _quote(converted_text, *args, **kwargs)
