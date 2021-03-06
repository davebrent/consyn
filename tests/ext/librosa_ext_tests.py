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
import unittest

try:
    from consyn.ext.librosa_ext import LibrosaFileLoader
    from consyn.ext.librosa_ext import LibrosaUnitLoader
    from consyn.ext.librosa_ext import LibrosaAnalyser
except ImportError:
    raise unittest.SkipTest("Librosa not installed")

from .loaders import FileLoaderTests
from .loaders import UnitLoaderTests
from .analysers import AnalyserTests


class LibrosaAnalyserTests(unittest.TestCase, AnalyserTests):
    Analyser = LibrosaAnalyser


class LibrosaFileLoaderTests(unittest.TestCase, FileLoaderTests):
    FileLoader = LibrosaFileLoader


class LibrosaUnitLoaderTests(unittest.TestCase, UnitLoaderTests):
    UnitLoader = LibrosaUnitLoader
