#!/usr/bin/env python
# Copyright 2013-2015 Julian Metzler

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

from setuptools import setup, find_packages

metadata = {}
with open('tweetpony/metadata.py') as f:
	exec(f.read(), metadata)

setup(
	name = metadata['name'],
	version = metadata['version'],
	description = metadata['description'],
	license = metadata['license'],
	author = metadata['author'],
	author_email = metadata['author_email'],
	install_requires = metadata['requires'],
	url = metadata['url'],
	keywords = metadata['keywords'],
	packages = find_packages(),
	use_2to3 = True,
)