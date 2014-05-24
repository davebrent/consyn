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
import collections
import math
import os
import unittest

from consyn.loaders import AubioFileLoader
from consyn.slicers import BeatSlicer
from consyn.slicers import OnsetSlicer
from consyn.slicers import RegularSlicer
from consyn.slicers import SlicerFactory

from . import SOUND_DIR


class OnsetSlicerTests(unittest.TestCase):

    def _onset_test(self, path, channels, expected_onsets, expected_duration):
        path = os.path.join(SOUND_DIR, path)

        result = [{"path": path}] \
            >> AubioFileLoader(hopsize=1024) \
            >> OnsetSlicer(
                winsize=1024,
                threshold=0,
                method="default") \
            >> list

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
        results = [{"path": os.path.join(SOUND_DIR, "amen-mono.wav")}] \
            >> AubioFileLoader(hopsize=hopsize) \
            >> OnsetSlicer(
                winsize=bufsize,
                hopsize=hopsize,
                method="default") \
            >> list

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
        results = [{"path": os.path.join(SOUND_DIR, case)}] \
            >> AubioFileLoader()

        frame_durs = collections.defaultdict(int)
        for res in results:
            frame = res["frame"]
            self.assertEqual(frame.samples.shape[0], frame.duration)
            frame_durs[frame.channel] += frame.samples.shape[0]

        self.assertEqual(frame_durs[0], duration)
        self.assertEqual(frame_durs[1], duration)

        slicer = OnsetSlicer()
        results = [{"path": os.path.join(SOUND_DIR, case)}] \
            >> AubioFileLoader() \
            >> slicer

        onset_durs = collections.defaultdict(int)
        for res in results:
            frame = res["frame"]
            self.assertEqual(frame.samples.shape[0], frame.duration)
            onset_durs[frame.channel] += frame.samples.shape[0]

        self.assertEqual(onset_durs[0], frame_durs[0])
        self.assertEqual(onset_durs[1], frame_durs[1])


class RegularSlicerTests(unittest.TestCase):

    @unittest.expectedFailure
    def test_simple_slices(self):
        path = os.path.join(SOUND_DIR, "amen-mono.wav")

        results = [{"path": path}] \
            >> AubioFileLoader(hopsize=1024) \
            >> RegularSlicer(winsize=2048) \
            >> list

        self.assertEqual(len(results), math.ceil(70560.0 / 2048.0))
        positions = [pool["frame"].position for pool in results]
        self.assertEqual(positions, [
            0, 2048, 4096, 6144, 8192, 10240, 12288, 14336, 16384, 18432,
            20480, 22528, 24576, 26624, 28672, 30720, 32768, 34816, 36864,
            38912, 40960, 43008, 45056, 47104, 49152, 51200, 53248, 55296,
            57344, 59392, 61440, 63488, 65536, 67584, 69632
        ])


class BeatSlicerTests(unittest.TestCase):

    def test_get_winsize(self):
        slicer = BeatSlicer()
        winsize = slicer.get_winsize(120, "1/16", 44100)
        self.assertEqual(winsize, 5513)
        self.assertTrue(True)

    def test_no_samplerate(self):
        slicer = BeatSlicer(bpm=120)
        error = False
        try:
            error = slicer.get_detector()
        except AssertionError:
            error = True
        self.assertTrue(error)

    def test_slice(self):
        path = os.path.join(SOUND_DIR, "amen-mono.wav")

        results = [{"path": path}] \
            >> AubioFileLoader(hopsize=512) \
            >> BeatSlicer(bpm=150, interval="1/16") \
            >> list

        positions = [pool["frame"].position for pool in results]
        self.assertEqual(positions, [
            0, 4410, 8820, 13230, 17640, 22050, 26460, 30870, 35280, 39690,
            44100, 48510, 52920, 57330, 61740, 66150
        ])


class SlicerFactoryTests(unittest.TestCase):

    def test_no_kargs(self):
        slicer = SlicerFactory("onsets")
        self.assertTrue(isinstance(slicer, OnsetSlicer))

        slicer = SlicerFactory("regular")
        self.assertTrue(isinstance(slicer, RegularSlicer))

        slicer = SlicerFactory("beats")
        self.assertTrue(isinstance(slicer, BeatSlicer))

    def test_kwargs(self):
        slicer = SlicerFactory("regular", winsize=9999)
        self.assertTrue(isinstance(slicer, RegularSlicer))
        self.assertEqual(slicer.winsize, 9999)

        slicer = SlicerFactory("onsets", winsize=9999, threshold=0,
                               method="energy")
        self.assertTrue(isinstance(slicer, OnsetSlicer))
        self.assertEqual(slicer.winsize, 9999)
        self.assertEqual(slicer.threshold, 0)
        self.assertEqual(slicer.method, "energy")

        slicer = SlicerFactory("beats", bpm=90, interval="1/16")
        self.assertEqual(slicer.bpm, 90)
        self.assertEqual(slicer.interval, "1/16")

    def test_wrong_kwargs(self):
        slicer = SlicerFactory("regular", foobar=9999)
        self.assertTrue(isinstance(slicer, RegularSlicer))

    def test_wrong_name(self):
        error = False
        try:
            error = SlicerFactory("foobar", foobar=9999)
        except:
            error = True
        self.assertTrue(error)
