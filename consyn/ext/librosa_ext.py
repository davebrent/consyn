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
from __future__ import unicode_literals

import librosa

from ..base import AnalysisStage
from ..base import AudioFrame
from ..base import FileLoaderStage
from ..base import Stage
from ..base import UnitLoaderStage
from ..slicers import BaseSlicer
from ..utils import slice_array


__all__ = [
    "LibrosaFeatures",
    "LibrosaFileLoader",
    "LibrosaOnsetSlicer",
    "LibrosaUnitLoader",
    "LibrosaWriter"
]


class LibrosaFileLoader(FileLoaderStage):

    def read(self, path):
        samples, samplerate = librosa.load(path, sr=None, mono=False)
        size = len(samples.shape)
        channels = 1

        if size != 1:
            channels = samples.shape[0]

        for channel in xrange(channels):
            position = 0

            if channels > 1:
                blocks = slice_array(samples[channel], hopsize=self.hopsize,
                                     bufsize=self.hopsize)
            else:
                blocks = slice_array(samples, hopsize=self.hopsize,
                                     bufsize=self.hopsize)

            for index, block in enumerate(blocks):
                duration = block.shape[0]

                frame = AudioFrame()
                frame.samplerate = samplerate
                frame.position = position
                frame.channel = channel
                frame.samples = block
                frame.duration = duration
                frame.index = index
                frame.path = path

                position += duration
                yield frame


class LibrosaUnitLoader(UnitLoaderStage):

    def read(self, path, unit):
        if not unit.mediafile:
            samplerate = 44100.0
        else:
            samplerate = float(unit.mediafile.samplerate)

        start = float(unit.position) / samplerate
        duration = float(unit.duration) / samplerate

        samples, samplerate = librosa.load(path, sr=samplerate, mono=False,
                                           offset=start, duration=duration)
        frame = AudioFrame()
        frame.samplerate = samplerate
        frame.position = unit.position
        frame.channel = unit.channel
        frame.duration = unit.duration
        frame.index = 0
        frame.path = path

        if len(samples.shape) == 1:
            frame.samples = samples
        else:
            frame.samples = samples[unit.channel]

        yield frame


class LibrosaOnsetSlicer(BaseSlicer):
    pass


class LibrosaFeatures(AnalysisStage):
    pass


class LibrosaWriter(Stage):
    pass
