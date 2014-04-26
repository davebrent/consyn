import math
import os
import unittest

import numpy

from consyn import pipeline
from consyn import tasks


SOUND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "sounds"))


class SoundfileTests(unittest.TestCase):

    def test_open_close_soundfile_task(self):
        path = os.path.join(SOUND_DIR, "amen-stereo.wav")
        initial = pipeline.State(initial={"path": path})
        soundfile = tasks.Soundfile(bufsize=1024, hopsize=1024)
        result = [initial] >> soundfile >> list

        self.assertEqual(len(result), 1)
        self.assertTrue("soundfile" in result[0].values)
        self.assertTrue(path in soundfile.soundfiles)
        soundfile.close()
        self.assertTrue(path not in soundfile.soundfiles)


class IterFramesTest(unittest.TestCase):

    def test_iterframes_in_order(self):
        path = os.path.join(SOUND_DIR, "amen-stereo.wav")
        soundfile = tasks.Soundfile(bufsize=1024, hopsize=1024)

        result = [pipeline.State(initial={"path": path})] \
            >> soundfile \
            >> tasks.IterFrames() \
            >> list

        soundfile.close()
        self.assertEqual(len(result), 138)

        previous = 0
        for state in result:
            self.assertTrue(previous <= state["index"])
            self.assertEqual(state["samplerate"], 44100)
            previous = state["index"]

        self.assertEqual(previous, 68)


class SegmentFramesTest(unittest.TestCase):

    def _onset_test(self, path, channels, expected_onsets, expected_duration):
        path = os.path.join(SOUND_DIR, path)
        soundfile = tasks.Soundfile(bufsize=1024, hopsize=1024)

        result = [pipeline.State(initial={"path": path})] \
            >> soundfile \
            >> tasks.IterFrames() \
            >> tasks.SegmentFrames(
                winsize=1024,
                threshold=0,
                min_slice_size=0,
                method="default") \
            >> list

        soundfile.close()
        self.assertEqual(len(result) / channels, expected_onsets)

        for i in range(channels):
            pos = -(i + 1)
            self.assertEqual(
                expected_duration,
                result[pos]["position"] + result[pos]["duration"])

    def test_simple_stereo_segments(self):
        self._onset_test("amen-stereo.wav", 2, 10, 70560)

    def test_simple_mono_segments(self):
        self._onset_test("amen-mono.wav", 1, 10, 70560)


class AnalyseSegmentsTest(unittest.TestCase):

    def test_same_buffersize(self):
        bufsize = 1024
        duration = 70560
        channels = 2
        path = os.path.join(SOUND_DIR, "amen-stereo.wav")

        soundfile = tasks.Soundfile(bufsize=bufsize, hopsize=bufsize)
        analysis = tasks.AnalyseSegments(winsize=bufsize, hopsize=bufsize)

        result = [pipeline.State(initial={"path": path})] \
            >> soundfile \
            >> tasks.IterFrames() \
            >> analysis \
            >> list

        soundfile.close()
        self.assertEqual(math.ceil(duration * channels / float(bufsize)),
                         len(result))

        for res in result:
            for method in analysis.methods:
                self.assertIsInstance(res["features"][method], numpy.float32)

    def test_different_sizes(self):
        bufsize = 1024
        path = os.path.join(SOUND_DIR, "amen-stereo.wav")

        soundfile = tasks.Soundfile(bufsize=bufsize, hopsize=bufsize)
        analysis = tasks.AnalyseSegments(winsize=1024, hopsize=512)

        result = [pipeline.State(initial={"path": path})] \
            >> soundfile \
            >> tasks.IterFrames() \
            >> tasks.SegmentFrames(
                winsize=1024,
                threshold=0,
                min_slice_size=0,
                method="default") \
            >> analysis \
            >> list

        soundfile.close()
        self.assertEqual(len(result), 20)

        for res in result:
            for method in analysis.methods:
                self.assertIsInstance(res["features"][method], numpy.float32)
