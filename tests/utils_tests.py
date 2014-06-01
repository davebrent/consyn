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
from consyn.commands import add_mediafile
from consyn.loaders import AubioUnitLoader
from consyn.models import MediaFile
from consyn.models import Unit
from consyn.utils import Concatenate
from consyn.utils import UnitGenerator

from . import DatabaseTests
from . import SOUND_DIR


class UnitGeneratorTests(DatabaseTests):

    def _test_iter_amount(self, name, num):
        path = os.path.join(SOUND_DIR, name)
        mediafile = add_mediafile(self.session, path, threshold=0)
        initial = [{"mediafile": mediafile}]
        results = initial >> UnitGenerator(self.session) >> list
        self.assertEqual(len(results), num)

    def test_stereo(self):
        self._test_iter_amount("amen-stereo.wav", 20)

    def test_mono(self):
        self._test_iter_amount("amen-mono.wav", 10)


class ConcatenateTests(DatabaseTests):

    def test_concatenate_file(self):
        path = os.path.join(SOUND_DIR, "hot_tamales.wav")
        mediafile = add_mediafile(self.session, path)
        self.session.flush()

        mediafile = [{"mediafile": mediafile}] \
            >> UnitGenerator(self.session) \
            >> AubioUnitLoader(
                key=lambda state: state["unit"].mediafile.path) \
            >> Concatenate() \
            >> list

    def test_internal_buffer(self):
        """Test initialization of internal buffer at the correct size"""
        concatenate = Concatenate()
        list(concatenate([
            {"frame": AudioFrame(samples=numpy.array([3] * 10)),
             "unit": Unit(channel=0, position=25, duration=10),
             "mediafile": MediaFile(duration=50, channels=2, path="test.wav")}
        ]))

        self.assertEqual(concatenate.buffers["test.wav"].shape, (2, 50))
        self.assertEqual(
            list(concatenate.buffers["test.wav"][0][25:35]), [3] * 10)

    def _test_clipper(self, samples, target_dur):
        concatenate = Concatenate()
        result = concatenate.clip_duration(samples, target_dur)
        self.assertEqual(result.shape[0], target_dur)
        return result

    def test_less_than(self):
        """Test clipping samples less than target duration"""
        result = self._test_clipper(numpy.arange(18), 20)
        self.assertEqual(list(numpy.arange(18)) + [0, 0], list(result))

    def test_more_than(self):
        """Test clipping samples more than target duration"""
        result = self._test_clipper(numpy.arange(25), 20)
        self.assertEqual(list(numpy.arange(20)), list(result))

    def test_equal(self):
        """Test clipping samples equal to target duration"""
        samples = numpy.arange(20)
        result = self._test_clipper(numpy.arange(20), 20)
        self.assertEqual(list(samples), list(result))
