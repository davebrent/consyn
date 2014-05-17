# -*- coding: utf-8 -*-
import unittest

import numpy

from consyn.models import Unit
from consyn.resynthesis import DurationClipper
from consyn.base import AudioFrame


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
