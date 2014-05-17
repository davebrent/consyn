# -*- coding: utf-8 -*-
import os
import unittest


from consyn.commands import add_mediafile
from consyn.utils import UnitGenerator

from . import SOUND_DIR
from . import DummySession


class UnitGeneratorTests(unittest.TestCase):

    def _test_iter_amount(self, name, num):
        session = DummySession()
        path = os.path.join(SOUND_DIR, name)
        mediafile = add_mediafile(session, path, threshold=0)
        initial = [{"mediafile": mediafile}]
        results = initial >> UnitGenerator(session) >> list
        self.assertEqual(len(results), num)

    def test_stereo(self):
        self._test_iter_amount("amen-stereo.wav", 20)

    def test_mono(self):
        self._test_iter_amount("amen-mono.wav", 10)
