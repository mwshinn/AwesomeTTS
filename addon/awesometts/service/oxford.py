# -*- coding: utf-8 -*-

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2015       Anki AwesomeTTS Development Team
# Copyright (C) 2015       Myrgy on GitHub
# Copyright (C) 2015       Dave Shifflett
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Service implementation for Oxford Dictionary
"""

__all__ = ['Oxford']

import re

from .base import Service
from .common import Trait

from HTMLParser import HTMLParser


RE_WHITESPACE = re.compile(r'[\0\s]+', re.UNICODE)


class OxfordLister(HTMLParser):
	def reset(self):
        	HTMLParser.reset(self)
		self.sounds = []

	def handle_starttag(self, tag, attrs):
		snd = [v for k, v in attrs if k=='data-src-mp3']
		if snd:
			self.sounds.extend(snd)

class Oxford(Service):
    """
    Provides a Service-compliant implementation for Oxford Dictionary.
    """

    __slots__ = []

    NAME = "Oxford Dictionary"

    TRAITS = [Trait.INTERNET]

    def desc(self):
        """
        Returns a short, static description.
        """

        return "Oxford Dictionary (British and American English)"

    def options(self):
        """
        Provides access to voice only.
        """

        voice_lookup = dict([
            # aliases for English, American
            (self.normalize(alias), 'en-US')
            for alias in ['American', 'American English', 'English, American',
                          'US']
        ] + [
            # aliases for English, British ("default" for the OED)
            (self.normalize(alias), 'en-GB')
            for alias in ['British', 'British English', 'English, British',
                          'English', 'en', 'en-EU', 'en-UK', 'EU', 'GB', 'UK']
        ])

        def transform_voice(value):
            """Normalize and attempt to convert to official code."""
            normalized = self.normalize(value)
            if normalized in voice_lookup:
                return voice_lookup[normalized]
            return value

        return [
            dict(
                key='voice',
                label="Voice",
                values=[('en-US', "English, American (en-US)"),
                        ('en-GB', "English, British (en-GB)")],
                default='en-GB',
                transform=transform_voice,
            ),
        ]

    def modify(self, text):
        """
        OED generally represents words with spaces using a dash between
        the words. Case usually doesn't matter, but sometimes it does,
        so we do not normalize it (e.g. "United-Kingdom" works but
        "united-kingdom" does not).
        """

        return RE_WHITESPACE.sub('-', text)

    def run(self, text, options, path):
        """
        Download wep page for given word
        Then extract mp3 path and download it
        """

        from urllib2 import quote
        dict_url = 'http://www.oxforddictionaries.com/definition/%s/%s' % (
            'american_english' if options['voice'] == 'en-US' else 'english',
            quote(text.encode('utf-8'))
        )

        parser = OxfordLister()
        parser.feed(self.net_stream(dict_url).decode('utf-8'))
        parser.close()

        if len(parser.sounds) > 0:
            sound_url = parser.sounds[0]
        
            self.net_download(
                path,
                sound_url,
                require=dict(mime='audio/mpeg', size=1024),
             )
        else:
            raise IOError("sound not found: " + dict_url)
