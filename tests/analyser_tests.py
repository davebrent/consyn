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
import unittest

import numpy

from consyn.base import Pipeline
from consyn.ext import Analyser
from consyn.ext import FileLoader
from consyn.slicers import slicer

from . import SOUND_DIR


class AnalyserTests(unittest.TestCase):

    def test_same_buffersize(self):
        bufsize = 1024
        path = os.path.join(SOUND_DIR, "amen-stereo.wav")

        analyser = Analyser(winsize=bufsize, hopsize=bufsize)

        pipeline = Pipeline([
            FileLoader(path, hopsize=bufsize),
            analyser,
            list
        ])

        result = pipeline.run()

        for res in result:
            for method in analyser.methods:
                self.assertIsInstance(res["features"][method], numpy.float32)

    def test_different_sizes(self):
        bufsize = 1024
        path = os.path.join(SOUND_DIR, "amen-stereo.wav")

        analyser = Analyser(winsize=1024, hopsize=512)

        pipeline = Pipeline([
            FileLoader(path, hopsize=bufsize),
            slicer(
                "beats",
                winsize=1024,
                threshold=0,
                method="default"),
            analyser,
            list
        ])

        result = pipeline.run()
        self.assertEqual(len(result), 24)

        for res in result:
            for method in analyser.methods:
                self.assertIsInstance(res["features"][method], numpy.float32)
