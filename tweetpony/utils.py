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
