# -*- coding: utf-8 -*-
import os
import unittest

import numpy

from consyn.loaders import AubioFrameLoader
from consyn.loaders import AubioUnitLoader
from consyn.models import Unit

from . import SOUND_DIR


class FrameLoaderTests(unittest.TestCase):

    def test_iterframes_in_order(self):
        path = os.path.join(SOUND_DIR, "amen-stereo.wav")

        result = [{"path": path}] \
            >> AubioFrameLoader(hopsize=1024) \
            >> list

        self.assertEqual(len(result), 138)

        previous = 0
        for pool in result:
            frame = pool["frame"]
            self.assertTrue(previous <= frame.index)
            self.assertEqual(frame.samplerate, 44100)
            previous = frame.index

        self.assertEqual(previous, 68)


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
