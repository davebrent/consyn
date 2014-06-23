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
import os

import numpy

from consyn.base import AudioFrame
from consyn.base import Pipeline
from consyn.commands import add_mediafile
from consyn.concatenators import BaseConcatenator
from consyn.concatenators import concatenator
from consyn.ext import UnitLoader
from consyn.models import MediaFile
from consyn.models import Unit
from consyn.utils import UnitGenerator

from . import DatabaseTests
from . import SOUND_DIR


class ConcatenateTests(DatabaseTests):

    def test_base(self):
        mediafile = MediaFile(duration=50, channels=2)
        base = BaseConcatenator(mediafile)
        self.assertRaises(NotImplementedError, base.concatenate, None, None)

    def test_concatenate_file(self):
        path = os.path.join(SOUND_DIR, "hot_tamales.wav")
        mediafile = add_mediafile(self.session, path, segmentation="beats")
        self.session.flush()

        concatenate = concatenator("clip", mediafile)

        pipeline = Pipeline([
            UnitGenerator(mediafile, self.session),
            UnitLoader(key=lambda state: state["unit"].mediafile.path),
            concatenate,
            list
        ])

        mediafile = pipeline.run()

    def test_internal_buffer(self):
        """Test initialization of internal buffer at the correct size"""
        mediafile = MediaFile(duration=50, channels=2, path="test.wav")
        concatenate = concatenator("clip", mediafile)

        list(concatenate([
            {"frame": AudioFrame(samples=numpy.array([3] * 10)),
             "unit": Unit(channel=0, position=25, duration=10)}
        ]))

        self.assertEqual(concatenate.buffer.shape, (2, 50))
        self.assertEqual(list(concatenate.buffer[0][25:35]), [3] * 10)

    def _test_clipper(self, samples, target):
        mediafile = MediaFile(duration=target.duration, channels=2,
                              path="test.wav")
        concatenate = concatenator("clip", mediafile)
        result = concatenate.clip_samples(samples, target.duration)
        self.assertEqual(result.shape[0], target.duration)
        return result

    def test_less_than(self):
        """Test clipping samples less than target duration"""
        target = Unit(duration=20)
        result = self._test_clipper(numpy.arange(18), target)
        self.assertEqual(list(numpy.arange(18)) + [0, 0], list(result))

    def test_more_than(self):
        """Test clipping samples more than target duration"""
        target = Unit(duration=20)
        result = self._test_clipper(numpy.arange(25), target)
        self.assertEqual(list(numpy.arange(20)), list(result))

    def test_equal(self):
        """Test clipping samples equal to target duration"""
        samples = numpy.arange(20)
        target = Unit(duration=20)
        result = self._test_clipper(numpy.arange(20), target)
        self.assertEqual(list(samples), list(result))
