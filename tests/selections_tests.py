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
import os

from consyn.selections import NearestNeighbour
from consyn.commands import add_mediafile

from . import SOUND_DIR
from . import DatabaseTests


class NearestNeighbourTests(DatabaseTests):

    def test_simple(self):
        path = os.path.join(SOUND_DIR, "amen-mono.wav")
        mediafile = add_mediafile(self.session, path)
        self.session.flush()

        selector = NearestNeighbour(self.session, [mediafile])
        for unit in mediafile.units:
            match = selector.select(unit)
            self.assertEqual(match.id, unit.id)
