# -*- coding: utf-8 -*-
import os
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from consyn.cli import commands
from consyn.models import Base
from . import SOUND_DIR


class CLITests(unittest.TestCase):

    def setUp(self):
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def test_simple(self):
        commands["add"](self.session, argv=[
            "add",
            os.path.join(SOUND_DIR, "amen-stereo.wav"),
            os.path.join(SOUND_DIR, "amen-mono.wav")])

        commands["ls"](self.session, argv=["ls"])
        commands["rm"](self.session, argv=["rm", "1", "2"])
