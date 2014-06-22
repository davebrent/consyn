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
import unittest

import numpy

from consyn.models import Unit
from consyn.resynthesis import Envelope
from consyn.resynthesis import TimeStretch


class EnvelopeTests(unittest.TestCase):

    def test_simple(self):
        envelope = Envelope()
        samples = numpy.array([1, 1, 1, 1, 1], dtype="float32")
        samples, _ = envelope.process(samples, None, None)
        self.assertEqual(list(samples), [1.0, 0.75, 0.5, 0.25, 0.0])


class TimestretchTests(unittest.TestCase):

    def test_equal_duration(self):
        timestretch = TimeStretch()
        target = Unit(duration=5)
        samples = numpy.array([1, 1, 1, 1, 1], dtype="float32")
        samples2, _ = timestretch.process(samples, None, target)
        self.assertEqual(list(samples), list(samples2))

    def test_constant_stretch_factor(self):
        timestretch = TimeStretch(factor=0.5)
        target = Unit(duration=4096)
        samples = numpy.zeros(2048, dtype="float32")
        samples.fill(1)

        samples2, _ = timestretch.process(samples, None, target)
        self.assertEqual(samples2.shape[0], 5120)

    def test_constant_stretch_with_equal_duration(self):
        timestretch = TimeStretch(factor=0.5)
        target = Unit(duration=2048)
        samples = numpy.zeros(2048, dtype="float32")
        samples.fill(1)

        samples2, _ = timestretch.process(samples, None, target)
        self.assertEqual(samples2.shape[0], 5120)
