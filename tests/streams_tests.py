import math
import os
import unittest

import numpy

from consyn import commands
from consyn import models
from consyn import streams

from . import SOUND_DIR
from . import DummySession


class FrameSampleReaderTest(unittest.TestCase):

    def test_iterframes_in_order(self):
        path = os.path.join(SOUND_DIR, "amen-stereo.wav")

        result = [{"path": path}] \
            >> streams.AubioFrameLoader(bufsize=1024, hopsize=1024) \
            >> list

        self.assertEqual(len(result), 138)

        previous = 0
        for pool in result:
            frame = pool["frame"]
            self.assertTrue(previous <= frame.index)
            self.assertEqual(frame.samplerate, 44100)
            previous = frame.index

        self.assertEqual(previous, 68)


class OnsetSlicerTest(unittest.TestCase):

    def _onset_test(self, path, channels, expected_onsets, expected_duration):
        path = os.path.join(SOUND_DIR, path)

        result = [{"path": path}] \
            >> streams.AubioFrameLoader(bufsize=1024, hopsize=1024) \
            >> streams.OnsetSlicer(
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

    def test_simple_stereo_segments(self):
        self._onset_test("amen-stereo.wav", 2, 10, 70560)

    def test_simple_mono_segments(self):
        self._onset_test("amen-mono.wav", 1, 10, 70560)


class RegularSlicerTest(unittest.TestCase):

    def test_simple_slices(self):
        path = os.path.join(SOUND_DIR, "amen-mono.wav")

        results = [{"path": path}] \
            >> streams.AubioFrameLoader(bufsize=1024, hopsize=1024) \
            >> streams.RegularSlicer(winsize=2048) \
            >> list

        self.assertEqual(len(results), math.ceil(70560.0 / 2048.0))
        positions = [pool["frame"].position for pool in results]
        self.assertEqual(positions, [
            0, 2048, 4096, 6144, 8192, 10240, 12288, 14336, 16384, 18432,
            20480, 22528, 24576, 26624, 28672, 30720, 32768, 34816, 36864,
            38912, 40960, 43008, 45056, 47104, 49152, 51200, 53248, 55296,
            57344, 59392, 61440, 63488, 65536, 67584, 69632
        ])


class BeatSlicerTest(unittest.TestCase):

    def test_get_winsize(self):
        slicer = streams.BeatSlicer()
        winsize = slicer.get_winsize(120, "1/16", 44100)
        self.assertEqual(winsize, 5513)
        self.assertTrue(True)

    def test_no_samplerate(self):
        slicer = streams.BeatSlicer(bpm=120)
        error = False
        try:
            error = slicer.get_detector()
        except AssertionError:
            error = True
        self.assertTrue(error)

    @unittest.expectedFailure
    def test_slice(self):
        path = os.path.join(SOUND_DIR, "amen-mono.wav")

        results = [{"path": path}] \
            >> streams.AubioFrameLoader(bufsize=1024, hopsize=1024) \
            >> streams.BeatSlicer(bpm=150, interval="1/16") \
            >> list

        positions = [pool["frame"].position for pool in results]
        self.assertEqual(positions, [
            0, 4410, 8820, 13230, 17640, 22050, 26460, 30870, 35280, 39690,
            44100, 48510, 52920, 57330, 61740, 66150
        ])


class SampleAnalyserTest(unittest.TestCase):

    def test_same_buffersize(self):
        bufsize = 1024
        duration = 70560
        channels = 2
        path = os.path.join(SOUND_DIR, "amen-stereo.wav")

        analyser = streams.SampleAnalyser(winsize=bufsize, hopsize=bufsize)

        result = [{"path": path}] \
            >> streams.AubioFrameLoader(bufsize=bufsize, hopsize=bufsize) \
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

        analyser = streams.SampleAnalyser(winsize=1024, hopsize=512)

        result = [{"path": path}] \
            >> streams.AubioFrameLoader(bufsize=bufsize, hopsize=bufsize) \
            >> streams.OnsetSlicer(
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


class UnitSampleReaderTests(unittest.TestCase):

    def test_read_whole_file(self):
        bufsize = 1024
        path = os.path.join(SOUND_DIR, "amen-stereo.wav")
        unit = models.Unit(channel=0, position=0, duration=70560)

        self.assertEqual(unit.duration, 70560)
        self.assertEqual(unit.channel, 0)
        self.assertEqual(unit.position, 0)

        initial = [{"path": path, "unit": unit}]
        loader = streams.AubioUnitLoader(bufsize=bufsize, hopsize=bufsize)
        result = initial >> loader >> list

        self.assertEqual(len(result), 1)
        samples = result[0]["frame"].samples

        self.assertEqual(samples.shape, (70560,))
        self.assertNotEqual(numpy.sum(samples), 0)

    def test_multiple_reads(self):
        reads = 10
        bufsize = 1024
        path = os.path.join(SOUND_DIR, "amen-stereo.wav")
        unit = models.Unit(channel=0, position=0, duration=70560)

        self.assertEqual(unit.duration, 70560)
        self.assertEqual(unit.channel, 0)
        self.assertEqual(unit.position, 0)

        loader = streams.AubioUnitLoader(bufsize=bufsize, hopsize=bufsize)

        for index in range(reads):
            initial = [{"path": path, "unit": unit}]
            result = initial >> loader >> list

            self.assertEqual(len(result), 1)
            samples = result[0]["frame"].samples

            self.assertEqual(samples.shape, (70560,))
            self.assertNotEqual(numpy.sum(samples), 0)

        self.assertEqual(index, reads - 1)


class UnitGeneratorTests(unittest.TestCase):

    def _test_iter_amount(self, name, num):
        session = DummySession()
        path = os.path.join(SOUND_DIR, name)
        mediafile = commands.add_mediafile(session, path)
        initial = [{"mediafile": mediafile}]
        results = initial >> streams.UnitGenerator(session) >> list
        self.assertEqual(len(results), num)

    def test_stereo(self):
        self._test_iter_amount("amen-stereo.wav", 20)

    def test_mono(self):
        self._test_iter_amount("amen-mono.wav", 10)


class DurationClipperTests(unittest.TestCase):

    def _test_simple(self, samples, unit_dur, unit_pos, target_dur,
                     target_pos):
        target = models.Unit(duration=target_dur, position=target_pos)
        unit = models.Unit(duration=unit_dur, position=unit_pos)

        pool = {
            "frame": streams.AudioFrame(samples=samples),
            "target": target,
            "unit": unit
        }

        results = [pool] >> streams.DurationClipper() >> list

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["frame"].samples.shape[0], target_dur)

    def test_less_than(self):
        self._test_simple(numpy.arange(18), 18, 3, 20, 2)

    def test_more_than(self):
        self._test_simple(numpy.arange(25), 25, 3, 20, 2)

    def test_equal(self):
        self._test_simple(numpy.arange(20), 20, 2, 20, 2)


class SlicerFactoryTests(unittest.TestCase):

    def test_no_kargs(self):
        slicer = streams.SlicerFactory("onsets")
        self.assertTrue(isinstance(slicer, streams.OnsetSlicer))

        slicer = streams.SlicerFactory("regular")
        self.assertTrue(isinstance(slicer, streams.RegularSlicer))

        slicer = streams.SlicerFactory("beats")
        self.assertTrue(isinstance(slicer, streams.BeatSlicer))

    def test_kwargs(self):
        slicer = streams.SlicerFactory("regular", winsize=9999)
        self.assertTrue(isinstance(slicer, streams.RegularSlicer))
        self.assertEqual(slicer.winsize, 9999)

        slicer = streams.SlicerFactory("onsets", winsize=9999, threshold=0,
                                       method="energy", min_slice_size=0)
        self.assertTrue(isinstance(slicer, streams.OnsetSlicer))
        self.assertEqual(slicer.winsize, 9999)
        self.assertEqual(slicer.threshold, 0)
        self.assertEqual(slicer.method, "energy")
        self.assertEqual(slicer.min_slice_size, 0)

        slicer = streams.SlicerFactory("beats", bpm=90, interval="1/16")
        self.assertEqual(slicer.bpm, 90)
        self.assertEqual(slicer.interval, "1/16")

    def test_wrong_kwargs(self):
        slicer = streams.SlicerFactory("regular", foobar=9999)
        self.assertTrue(isinstance(slicer, streams.RegularSlicer))

    def test_wrong_name(self):
        error = False
        try:
            error = streams.SlicerFactory("foobar", foobar=9999)
        except:
            error = True
        self.assertTrue(error)
