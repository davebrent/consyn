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
import os
import unittest

import numpy

from consyn.loaders import AubioFileLoader
from consyn.loaders import AubioUnitLoader
from consyn.models import Unit

from . import SOUND_DIR


class FileLoaderTests(unittest.TestCase):

    def test_iterframes_in_order(self):
        path = os.path.join(SOUND_DIR, "amen-stereo.wav")

        result = [{"path": path}] \
            >> AubioFileLoader(hopsize=1024) \
            >> list

        self.assertEqual(len(result), 138)

        previous = 0
        for pool in result:
            frame = pool["frame"]
            self.assertTrue(previous <= frame.index)
            self.assertEqual(frame.samplerate, 44100)
            previous = frame.index

        self.assertEqual(previous, 68)

    def test_duration_equal_samples_length(self):
        """Test duration is always equal to length of samples array"""
        path = os.path.join(SOUND_DIR, "cant_let_you_use_me.wav")
        results = [{"path": path}] >> AubioFileLoader()
        for res in results:
            frame = res["frame"]
            self.assertEqual(frame.duration, frame.samples.shape[0])

    def test_channels_zero_indexed(self):
        """Test channels are zero indexed"""
        path = os.path.join(SOUND_DIR, "amen-stereo.wav")
        results = [{"path": path}] >> AubioFileLoader(hopsize=1024)
        channels = set([res["frame"].channel for res in results])
        self.assertEqual(channels, set([0, 1]))


class UnitLoaderTests(unittest.TestCase):

    def test_read_whole_file(self):
        bufsize = 1024
        path = os.path.join(SOUND_DIR, "amen-stereo.wav")
        unit = Unit(channel=0, position=0, duration=70560)

        self.assertEqual(unit.duration, 70560)
        self.assertEqual(unit.channel, 0)
        self.assertEqual(unit.position, 0)

        initial = [{"path": path, "unit": unit}]
        loader = AubioUnitLoader(hopsize=bufsize)
        result = initial >> loader >> list

        self.assertEqual(len(result), 1)
        samples = result[0]["frame"].samples

        self.assertEqual(samples.shape, (70560,))
        self.assertNotEqual(numpy.sum(samples), 0)

    def test_multiple_reads(self):
        reads = 10
        bufsize = 1024
        path = os.path.join(SOUND_DIR, "amen-stereo.wav")
        unit = Unit(channel=0, position=0, duration=70560)

        self.assertEqual(unit.duration, 70560)
        self.assertEqual(unit.channel, 0)
        self.assertEqual(unit.position, 0)

        loader = AubioUnitLoader(hopsize=bufsize)

        for index in range(reads):
            initial = [{"path": path, "unit": unit}]
            result = initial >> loader >> list

            self.assertEqual(len(result), 1)
            samples = result[0]["frame"].samples

            self.assertEqual(samples.shape, (70560,))
            self.assertNotEqual(numpy.sum(samples), 0)

        self.assertEqual(index, reads - 1)
