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
import collections
import os
import unittest

from consyn.base import Pipeline
from consyn.slicers import slicer

try:
    from consyn.ext.aubio_ext import AubioOnsetSlicer
    from consyn.ext.aubio_ext import AubioFileLoader
    from consyn.ext.aubio_ext import AubioUnitLoader
    from consyn.ext.aubio_ext import AubioAnalyser
except ImportError:
    raise unittest.SkipTest("Aubio not installed")

from .. import SOUND_DIR
from .loaders import FileLoaderTests
from .loaders import UnitLoaderTests
from .analysers import AnalyserTests


class AubioAnalyserTests(unittest.TestCase, AnalyserTests):
    Analyser = AubioAnalyser


class AubioFileLoaderTests(unittest.TestCase, FileLoaderTests):
    FileLoader = AubioFileLoader


class AubioUnitLoaderTests(unittest.TestCase, UnitLoaderTests):
    UnitLoader = AubioUnitLoader


class AubioOnsetSlicerTests(unittest.TestCase):

    def _onset_test(self, path, channels, expected_onsets, expected_duration):
        path = os.path.join(SOUND_DIR, path)

        pipeline = Pipeline([
            AubioFileLoader(path, hopsize=1024),
            AubioOnsetSlicer(
                winsize=1024,
                threshold=0,
                method="default"),
            list
        ])

        result = pipeline.run()
        self.assertEqual(len(result) / channels, expected_onsets)

        for i in range(channels):
            pos = -(i + 1)
            self.assertEqual(
                expected_duration,
                result[pos]["frame"].position + result[pos]["frame"].duration)

        return result

    def test_simple_stereo_segments(self):
        self._onset_test("amen-stereo.wav", 2, 10, 70560)

    def test_simple_mono_segments(self):
        self._onset_test("amen-mono.wav", 1, 10, 70560)

    def test_same_as_aubioonset(self):
        """Deteted onsets should be similar to those detected by aubioonset"""
        bufsize = 512
        hopsize = 256

        pipeline = Pipeline([
            AubioFileLoader(
                os.path.join(SOUND_DIR, "amen-mono.wav"),
                hopsize=hopsize),
            AubioOnsetSlicer(
                winsize=bufsize,
                hopsize=hopsize,
                method="default"),
            list
        ])

        results = pipeline.run()

        # values from aubioonset & aubio/demos/demo_onset.py
        self.assertEqual(map(lambda r: r["frame"].position, results), [
            0, 8657, 17410, 26321, 30819, 35069, 39755, 43934, 52727, 61561
        ])

    def test_flush_1(self):
        self._test_all_samples_flushed("cant_let_you_use_me.wav", 160768)

    def test_flush_2(self):
        self._test_all_samples_flushed("hand_clapping_song.wav", 458496)

    def test_flush_3(self):
        self._test_all_samples_flushed("hot_tamales.wav", 134912)

    def test_flush_4(self):
        self._test_all_samples_flushed("right on.wav", 508686)

    def test_flush_5(self):
        self._test_all_samples_flushed("rimbo.wav", 216931)

    def test_flush_6(self):
        self._test_all_samples_flushed("we_laugh_at_danger.wav", 113515)

    def _test_all_samples_flushed(self, case, duration):
        """Test all samples are outputted by onset slicer"""
        pipeline = Pipeline([
            AubioFileLoader(os.path.join(SOUND_DIR, case))
        ])

        results = pipeline.run()

        frame_durs = collections.defaultdict(int)
        for res in results:
            frame = res["frame"]
            self.assertEqual(frame.samples.shape[0], frame.duration)
            frame_durs[frame.channel] += frame.samples.shape[0]

        self.assertEqual(frame_durs[0], duration)
        self.assertEqual(frame_durs[1], duration)

        onset_slicer = AubioOnsetSlicer()

        pipeline = Pipeline([
            AubioFileLoader(os.path.join(SOUND_DIR, case)),
            onset_slicer
        ])

        results = pipeline.run()

        onset_durs = collections.defaultdict(int)
        for res in results:
            frame = res["frame"]
            self.assertEqual(frame.samples.shape[0], frame.duration)
            onset_durs[frame.channel] += frame.samples.shape[0]

        self.assertEqual(onset_durs[0], frame_durs[0])
        self.assertEqual(onset_durs[1], frame_durs[1])

    def test_slicer_factory(self):
        slicer_instance = slicer("onsets")
        self.assertTrue(isinstance(slicer_instance, AubioOnsetSlicer))

    def test_slicer_kwargs(self):
        slicer_instance = slicer("onsets", winsize=9999, threshold=0,
                                 method="energy")
        self.assertTrue(isinstance(slicer_instance, AubioOnsetSlicer))
        self.assertEqual(slicer_instance.winsize, 9999)
        self.assertEqual(slicer_instance.threshold, 0)
        self.assertEqual(slicer_instance.method, "energy")
