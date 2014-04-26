import os

SOUND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "sounds"))


class DummySession(object):
    def add(self, obj):
        pass
