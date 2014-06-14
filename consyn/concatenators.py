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
import numpy

from .base import Stage
from .base import StageFactory
from .settings import DTYPE


__all__ = ["ConcatenatorFactory"]


class BaseConcatenator(Stage):

    def __init__(self, mediafile, unit_key="unit"):
        super(BaseConcatenator, self).__init__()
        self.mediafile = mediafile
        self.unit_key = unit_key
        self.buffer = self.initialize_buffer(self.mediafile)

    def __call__(self, pipe):
        for pool in pipe:
            target = pool[self.unit_key]
            self.concatenate(target, pool["frame"].samples)

        yield {
            "mediafile": self.mediafile,
            "buffer": self.buffer
        }

    def initialize_buffer(self, mediafile):
        return numpy.zeros(
            (mediafile.channels, mediafile.duration), dtype=DTYPE)

    def concatenate(self, target, samples):
        raise NotImplementedError("Concatenators must implement this")


class ClipConcatenator(BaseConcatenator):

    def concatenate(self, target, samples):
        start = target.position
        end = target.position + target.duration

        samples = self.clip_samples(samples, target.duration)
        self.buffer[target.channel][start:end] = samples

    def clip_samples(self, arr, length):
        actual = arr.shape[0]
        tmp = numpy.zeros(length, dtype=DTYPE)

        if actual < length:
            tmp[0:actual] = arr
        elif actual > length:
            tmp[0:length] = arr[0:length]
        else:
            tmp = arr

        return tmp


class OverlayConcatenator(BaseConcatenator):
    pass


class StackConcatenator(BaseConcatenator):
    pass


class ConcatenatorFactory(StageFactory):
    objects = {
        "clip": ClipConcatenator,
        "overlay": OverlayConcatenator,
        "stack": StackConcatenator
    }
