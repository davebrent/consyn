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

import aubio
import numpy

from .base import Stage


__all__ = [
    "UnitGenerator",
    "AubioWriter"
]


class UnitGenerator(Stage):

    def __init__(self, mediafile, session):
        super(UnitGenerator, self).__init__()
        self.mediafile = mediafile
        self.session = session

    def __call__(self, *args):
        for unit in self.mediafile.units:
            yield {"unit": unit}


class AubioWriter(Stage):

    def __init__(self, mediafile, outfile):
        super(AubioWriter, self).__init__()
        self.outfile = outfile
        self.mediafile = mediafile

    def __call__(self, pipe):
        for pool in pipe:
            framesize = 2048
            buff = pool["buffer"]

            sink = aubio.sink(self.outfile, 0, self.mediafile.channels)
            out_samples = numpy.array_split(
                buff, int(float(self.mediafile.duration) / int(framesize)),
                axis=1)

            for frame in out_samples:
                amount = frame[0].shape[0]
                sink.do_multi(frame, amount)

            sink.close()
            del sink

            yield {"out": self.outfile}
