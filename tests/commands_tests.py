import os
import unittest
from consyn import commands

from . import SOUND_DIR
from . import DummySession


class AddCorpusTests(unittest.TestCase):

    def _test_file(self, name, num_units, samplerate, num_channels, duration):
        path = os.path.join(SOUND_DIR, name)
        session = DummySession()
        mediafile = commands.add_mediafile(session, path, threshold=0)

        self.assertEqual(len(mediafile.units), num_units)
        self.assertEqual(len(mediafile.features), num_units)
        self.assertEqual(mediafile.samplerate, samplerate)
        self.assertEqual(mediafile.channels, num_channels)
        self.assertEqual(mediafile.path, path)
        self.assertEqual(mediafile.duration, duration)

        _duration = 0
        for unit in mediafile.units:
            _duration += unit.duration
        self.assertEqual(_duration, mediafile.duration * mediafile.channels)

    def test_stereo_mediafile(self):
        self._test_file("amen-stereo.wav", 20, 44100, 2, 70560)

    def test_mono_mediafile(self):
        self._test_file("amen-mono.wav", 10, 44100, 1, 70560)
