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
import aubio
import numpy

from .base import Stage
from .models import MediaFile
from .settings import DTYPE


__all__ = [
    "UnitGenerator",
    "MediaFileSampleBuilder",
    "MediaFileWriter"
]


class UnitGenerator(Stage):

    def __init__(self, session):
        super(UnitGenerator, self).__init__()
        self.session = session

    def __call__(self, pipe):
        for pool in pipe:
            if not isinstance(pool["mediafile"], MediaFile):
                pool["mediafile"] = MediaFile.by_id_or_name(
                    self.session, pool["mediafile"])

            for unit in pool["mediafile"].units:
                pool["unit"] = unit
                yield pool


class MediaFileSampleBuilder(Stage):

    def __init__(self, unit_key="unit", channels=2):
        super(MediaFileSampleBuilder, self).__init__()
        self.unit_key = unit_key
        self.channels = channels
        self.buffers = {}
        self.counts = {}
        self.end = {}

    def __call__(self, pipe):
        for pool in pipe:
            mediafile = pool["mediafile"]
            target = pool[self.unit_key]
            samples = pool["frame"].samples

            if mediafile.path in self.end:
                continue

            if mediafile.path not in self.buffers:
                self.counts[mediafile.path] = 0
                self.buffers[mediafile.path] = numpy.zeros(
                    (mediafile.channels, mediafile.duration),
                    dtype=DTYPE)

            buff = self.buffers[mediafile.path]
            buff[target.channel][
                target.position:target.position + target.duration] = samples
            self.counts[mediafile.path] += 1

            if self.counts[mediafile.path] == (len(mediafile.units) - 1) and \
                    mediafile.path not in self.end:
                self.end[mediafile.path] = True
                new_pool = {
                    "mediafile": pool["mediafile"],
                    "buffer": buff
                }

                if pool.get("out"):
                    new_pool["out"] = pool["out"]

                yield new_pool


class MediaFileWriter(Stage):

    def __call__(self, pipe):
        for pool in pipe:
            framesize = 1024
            mediafile = pool["mediafile"]
            buff = pool["buffer"]
            outfile = pool["out"]

            sink = aubio.sink(outfile, 0, mediafile.channels)
            out_samples = numpy.array_split(buff, framesize, axis=1)

            for frame in out_samples:
                amount = frame[0].shape[0]
                sink.do_multi(frame, amount)

            sink.close()
            del sink

            yield {"out": pool["out"]}
