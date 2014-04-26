import os
import unittest
from consyn import commands


SOUND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "sounds"))


class DummySession(object):
    def add(self, obj):
        pass


class AddCorpusTests(unittest.TestCase):

    def test_stereo_corpus(self):
        path = os.path.join(SOUND_DIR, "amen-stereo.wav")
        session = DummySession()
        corpus = commands.add_corpus(session, path)

        self.assertEqual(len(corpus.units), 20)
        self.assertEqual(len(corpus.features), 20)
        self.assertEqual(corpus.samplerate, 44100)
        self.assertEqual(corpus.channels, 2)
        self.assertEqual(corpus.path, path)

    def test_mono_corpus(self):
        path = os.path.join(SOUND_DIR, "amen-mono.wav")
        session = DummySession()
        corpus = commands.add_corpus(session, path)

        self.assertEqual(len(corpus.units), 10)
        self.assertEqual(len(corpus.features), 10)
        self.assertEqual(corpus.samplerate, 44100)
        self.assertEqual(corpus.channels, 1)
        self.assertEqual(corpus.path, path)
