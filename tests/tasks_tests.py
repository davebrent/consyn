import os
import unittest
from consyn import tasks
from consyn import pipeline


SOUND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "sounds"))


class SoundfileTests(unittest.TestCase):

    def test_open_close_soundfile_task(self):
        path = os.path.join(SOUND_DIR, "amen.wav")
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
        path = os.path.join(SOUND_DIR, "amen.wav")
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
