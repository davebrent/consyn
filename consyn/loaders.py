# -*- coding: utf-8 -*-
# Copyright (C) 2014, David Poulter
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
"""Classes for generating streams of AudioFrames"""
import logging

import aubio
import numpy

from .base import AudioFrame
from .base import FileLoaderStage
from .base import UnitLoaderStage
from .settings import DTYPE
from .settings import OPEN_FILE_MAX


__all__ = [
    "AubioFileLoader",
    "AubioUnitLoader"
]


logger = logging.getLogger(__name__)


class AubioFileCache(object):

    _soundfiles = {}
    _counts = {}

    def open(self, path, hopsize):
        if path not in self._soundfiles:
            soundfile = aubio.source(path, 0, hopsize)
            self._soundfiles[path] = soundfile
            self._counts[path] = 0
        if len(self._soundfiles) > OPEN_FILE_MAX:
            minimum = float("inf")
            min_path = None
            for path in self._counts:
                if minimum > self._counts[path]:
                    minimum = self._counts[path]
                    min_path = path
            self._close(min_path)

        self._counts[path] += 1
        return self._soundfiles[path]

    def close(self):
        for path in self._soundfiles.keys():
            self._close(path)

    def _close(self, path):
        self._soundfiles[path].close()
        del self._soundfiles[path]
        del self._counts[path]


class AubioFileLoader(FileLoaderStage, AubioFileCache):

    def read(self, path):
        soundfile = self.open(path, self.hopsize)
        soundfile.seek(0)

        index = 0
        positions = {}

        while True:
            channels, read = soundfile.do_multi()

            if read == 0:
                break

            for channel, samples in enumerate(channels):
                if channel not in positions:
                    positions[channel] = 0

                frame = AudioFrame()
                frame.samplerate = soundfile.samplerate
                frame.position = positions[channel]
                frame.channel = channel
                frame.samples = samples[:read]
                frame.duration = read
                frame.index = index
                frame.path = path

                positions[channel] += read
                yield frame

            index += 1
            if read < soundfile.hop_size:
                break

        logger.debug("Closing soundfile for {}".format(path))


class AubioUnitLoader(UnitLoaderStage, AubioFileCache):

    def read(self, path, unit):
        soundfile = self.open(path, self.hopsize)
        soundfile.seek(unit.position)

        pos = 0
        buff = numpy.zeros(unit.duration, dtype=DTYPE)

        while True:
            channels, read = soundfile.do_multi()
            samples = channels[unit.channel]

            if read + pos > unit.duration:
                read = unit.duration - pos

            buff[pos:pos + read] = samples[:read]
            pos += read

            if pos >= unit.duration or read == 0:
                break

        frame = AudioFrame()
        frame.samplerate = soundfile.samplerate
        frame.position = unit.position
        frame.channel = unit.channel
        frame.samples = buff
        frame.duration = unit.duration
        frame.index = 0
        frame.path = path

        logger.debug("Closing soundfile for {}".format(path))
        yield frame
