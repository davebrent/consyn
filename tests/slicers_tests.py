# -*- coding: utf-8 -*-
import math
import os
import unittest

from consyn.loaders import AubioFrameLoader
from consyn.slicers import OnsetSlicer
from consyn.slicers import RegularSlicer
from consyn.slicers import BeatSlicer
from consyn.slicers import SlicerFactory

from . import SOUND_DIR


class OnsetSlicerTests(unittest.TestCase):

    def _onset_test(self, path, channels, expected_onsets, expected_duration):
        path = os.path.join(SOUND_DIR, path)

        result = [{"path": path}] \
            >> AubioFrameLoader(hopsize=1024) \
            >> OnsetSlicer(
                winsize=1024,
                threshold=0,
                min_slice_size=0,
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
            >> AubioFrameLoader(hopsize=hopsize) \
            >> OnsetSlicer(
                winsize=bufsize,
                hopsize=hopsize,
                method="default") \
            >> list

        # values from aubioonset & aubio/demos/demo_onset.py
        self.assertEqual(map(lambda r: r["frame"].position, results), [
            0, 8657, 17410, 26321, 30819, 35069, 39755, 43934, 52727, 61561
        ])


class RegularSlicerTests(unittest.TestCase):

    def test_simple_slices(self):
        path = os.path.join(SOUND_DIR, "amen-mono.wav")

        results = [{"path": path}] \
            >> AubioFrameLoader(hopsize=1024) \
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
            >> AubioFrameLoader(hopsize=512) \
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
                               method="energy", min_slice_size=0)
        self.assertTrue(isinstance(slicer, OnsetSlicer))
        self.assertEqual(slicer.winsize, 9999)
        self.assertEqual(slicer.threshold, 0)
        self.assertEqual(slicer.method, "energy")
        self.assertEqual(slicer.min_slice_size, 0)

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
