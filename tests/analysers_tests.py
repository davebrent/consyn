# -*- coding: utf-8 -*-
import math
import os
import unittest

import numpy

from consyn.loaders import AubioFrameLoader
from consyn.slicers import OnsetSlicer
from consyn.analysers import SampleAnalyser

from . import SOUND_DIR


class SampleAnalyserTests(unittest.TestCase):

    def test_same_buffersize(self):
        bufsize = 1024
        duration = 70560
        channels = 2
        path = os.path.join(SOUND_DIR, "amen-stereo.wav")

        analyser = SampleAnalyser(winsize=bufsize, hopsize=bufsize)

        result = [{"path": path}] \
            >> AubioFrameLoader(hopsize=bufsize) \
            >> analyser \
            >> list

        self.assertEqual(math.ceil(duration * channels / float(bufsize)),
                         len(result))

        for res in result:
            for method in analyser.methods:
                self.assertIsInstance(res["features"][method], numpy.float32)

    def test_different_sizes(self):
        bufsize = 1024
        path = os.path.join(SOUND_DIR, "amen-stereo.wav")

        analyser = SampleAnalyser(winsize=1024, hopsize=512)

        result = [{"path": path}] \
            >> AubioFrameLoader(hopsize=bufsize) \
            >> OnsetSlicer(
                winsize=1024,
                threshold=0,
                min_slice_size=0,
                method="default") \
            >> analyser \
            >> list

        self.assertEqual(len(result), 20)

        for res in result:
            for method in analyser.methods:
                self.assertIsInstance(res["features"][method], numpy.float32)
