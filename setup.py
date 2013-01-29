#!/usr/bin/env python
# Copyright (C) 2013 Julian Metzler
# See the LICENSE file for the full license.

from tweetpony import metadata
from setuptools import setup, find_packages

setup(
	name = metadata.name,
	version = metadata.version,
	description = metadata.description,
	license = metadata.license,
	author = metadata.author,
	author_email = metadata.author_email,
	url = metadata.url,
	keywords = metadata.keywords,
	packages = find_packages(),
)
