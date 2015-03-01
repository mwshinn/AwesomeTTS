# -*- coding: utf-8 -*-

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2015       Anki AwesomeTTS Development Team
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
Service implementation for the Wikimedia Commons
"""

__all__ = ['Wiki']

from re import compile as re_compile

from .base import Service
from .common import Trait


# Maps various AwesomeTTS-based language codes to search prefixes known
# to be in relatively large abundance on the Wikimedia Commons; most-commonly
# used prefixes should be listed first. Additionally, the keys should be the
# loosest prefix possible (as the run() implementation uses this during its
# fallback search).

LOOKUP = {
    'de': ("German", ['de']),
    'es': ("Spanish",
           ['es', 'es-am-lat', 'es-chile', 'es-us', 'es-mx', 'es-cl']),
    'en': ("English",
           ['en', 'en-us', 'en-uk', 'en-gb', 'en-au']),
    'fr': ("French", ['fr']),
    'it': ("Italian", ['it']),
    'pt': ("Portuguese", ['pt', 'pt-br', 'pt-pt']),
    'zh': ("Chinese", ['zh']),
}


# Pattern for matching links to audio files. Intentionally excludes files that
# are longer than 59 seconds (which are usually articles being spoken, rather
# than the spoken version of what the user searched for).

RE_FILE_LINK = re_compile(r'href="/wiki/File:([^"]+\.ogg)".*'
                          r'sound file, \d{1,2}(\.\d)? s')


class Wiki(Service):
    """
    Provides a Service-compliant implementation for the Wikimedia
    Commons.
    """

    __slots__ = [
        '_cache',  # dict mapping search inputs to resulting file, if any
    ]

    NAME = "Wikimedia Commons"

    TRAITS = [Trait.INTERNET, Trait.TRANSCODING]

    def __init__(self, *args, **kwargs):
        super(Wiki, self).__init__(*args, **kwargs)
        self._cache = {}

    def desc(self):
        """Returns a short, static description."""

        return "File search on the Wikimedia Commons; experimental with " \
               "limited word availability"

    def options(self):
        """Provides access to voice and strictness."""

        voice_lookup = {self.normalize(code): code for code in LOOKUP.keys()}

        def transform_voice(value):
            """Normalize and attempt to convert to official code."""

            normalized = self.normalize(value)[0:2]
            return (voice_lookup[normalized] if normalized in voice_lookup
                    else value)

        return [
            dict(
                key='voice',
                label="Voice",
                values=[(code, "%s (%s)" % (name, code))
                        for code, (name, dummy) in sorted(LOOKUP.items())],
                transform=transform_voice,
            ),
        ]

    def run(self, text, options, path):
        """
        Searches Wikimedia Commons for files that match the input
        phrase, trying several prefixes that are known to work for the
        given language.
        """

        if len(text) > 100:
            raise IOError("Input text is too long for the Wikimedia Commons")

        cache = self._cache
        text = text.replace('"', '')  # quotes reserved for search mechanics

        def search(query):
            """Returns Commons filename for search, if any found."""

            if query not in cache:
                capture = RE_FILE_LINK.search(self.net_stream(
                    ('https://commons.wikimedia.org/w/', {'search': query}),
                    require=dict(mime='text/html', size=1024),
                ))
                cache[query] = capture.group(1) if capture else None

            return cache[query]

        primary = options['voice']
        prefixes = LOOKUP[primary][1]

        for prefix in prefixes:
            # tight search using only the prefixes
            filename = search('intitle:.ogg prefix:"file:%s-%s"' %
                              (prefix, text))
            if filename:
                break

        else:
            # fallback using the loose prefix and "anywhere in title" match
            filename = search('intitle:"%s" intitle:.ogg prefix:file:%s' %
                              (text, primary))

            if not filename:
                # try one final time using the entire text area
                filename = search('%s intitle:.ogg prefix:file:%s' %
                                  (text, primary))

        if not filename:
            raise IOError(
                "Cannot find anything on the Wikimedia Commons for this "
                "phrase. For phrases, you may want to try another service."
                if text.count(' ')
                else "Cannot find this word on the Wikimedia Commons."
            )

        from hashlib import md5
        from urllib import unquote
        digest = md5(unquote(filename)).hexdigest()

        try:
            output_wav = self.path_temp('wav')

            self.net_dump(
                output_wav,
                'http://upload.wikimedia.org/wikipedia/commons/%s/%s/%s' %
                (digest[0:1], digest[0:2], filename),
            )

            self.cli_transcode(output_wav, path, require=dict(size_in=1024))

        finally:
            self.path_unlink(output_wav)
