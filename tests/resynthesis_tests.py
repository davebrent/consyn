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
import unittest

import numpy

from consyn.base import AudioFrame
from consyn.models import Unit
from consyn.resynthesis import DurationClipper
from consyn.resynthesis import Envelope


class DurationClipperTests(unittest.TestCase):

    def _test_simple(self, samples, unit_dur, unit_pos, target_dur,
                     target_pos):
        target = Unit(duration=target_dur, position=target_pos)
        unit = Unit(duration=unit_dur, position=unit_pos)

        pool = {
            "frame": AudioFrame(samples=samples),
            "target": target,
            "unit": unit
        }

        results = [pool] >> DurationClipper() >> list

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["frame"].samples.shape[0], target_dur)
        return results[0]["frame"].samples

    def test_less_than(self):
        result = self._test_simple(numpy.arange(18), 18, 3, 20, 2)
        self.assertEqual(list(numpy.arange(18)) + [0, 0], list(result))

    def test_more_than(self):
        result = self._test_simple(numpy.arange(25), 25, 3, 20, 2)
        self.assertEqual(list(numpy.arange(20)), list(result))

    def test_equal(self):
        samples = numpy.arange(20)
        result = self._test_simple(numpy.arange(20), 20, 2, 20, 2)
        self.assertEqual(list(samples), list(result))


class EnvelopeTests(unittest.TestCase):

    def test_simple(self):
        envelope = Envelope()
        samples = numpy.array([1, 1, 1, 1, 1], dtype="float32")
        samples, _ = envelope.process(samples, None, None)
        self.assertEqual(list(samples), [1.0, 0.75, 0.5, 0.25, 0.0])
