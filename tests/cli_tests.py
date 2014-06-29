# -*- coding: utf-8 -*-
# Copyright (C) 2014, David Poulter
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import unicode_literals
import os
import unittest

from click.testing import CliRunner

from consyn.cli import main

from . import SOUND_DIR


class CLITests(unittest.TestCase):

    def setUp(self):
        self.database = "--database=sqlite:///:memory:"

    def test_simple(self):
        sound1 = os.path.join(SOUND_DIR, "amen-stereo.wav")
        sound2 = os.path.join(SOUND_DIR, "amen-mono.wav")

        runner = CliRunner()
        result = runner.invoke(main, [
            "--verbose", self.database, "add", sound1])
        self.assertEqual(result.exception, None)
        self.assertEqual(result.exit_code, 0)

        result = runner.invoke(main, [
            "--verbose", self.database, "add", sound2])
        self.assertEqual(result.exception, None)
        self.assertEqual(result.exit_code, 0)

        result = runner.invoke(main, ["--verbose", self.database, "ls"])
        self.assertEqual(result.exception, None)
        self.assertEqual(result.exit_code, 0)

        result = runner.invoke(main, [
            "--verbose", self.database, "rm", "1", "2"])
        self.assertEqual(result.exception, None)
        self.assertEqual(result.exit_code, 0)
