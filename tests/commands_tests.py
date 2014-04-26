import os
import unittest
from consyn import commands


SOUND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "sounds"))


class DummySession(object):
    def add(self, obj):
        pass


class AddCorpusTests(unittest.TestCase):

    def _test_file(self, name, num_units, samplerate, num_channels, duration):
        path = os.path.join(SOUND_DIR, name)
        session = DummySession()
        corpus = commands.add_corpus(session, path)

        self.assertEqual(len(corpus.units), num_units)
        self.assertEqual(len(corpus.features), num_units)
        self.assertEqual(corpus.samplerate, samplerate)
        self.assertEqual(corpus.channels, num_channels)
        self.assertEqual(corpus.path, path)
        self.assertEqual(corpus.duration, duration)

        _duration = 0
        for unit in corpus.units:
            _duration += unit.duration
        self.assertEqual(_duration, corpus.duration * corpus.channels)

    def test_stereo_corpus(self):
        self._test_file("amen-stereo.wav", 20, 44100, 2, 70560)

    def test_mono_corpus(self):
        self._test_file("amen-mono.wav", 10, 44100, 1, 70560)
