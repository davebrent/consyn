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

from consyn.commands import add_mediafile
from consyn.commands import cluster_units
from consyn.models import Features

from . import SOUND_DIR
from . import DatabaseTests


class AddMediaFileTests(DatabaseTests):

    def _test_file(self, name, num_units, samplerate, num_channels, duration):
        path = os.path.join(SOUND_DIR, name)
        mediafile = add_mediafile(self.session, path, segmentation="beats")

        self.assertEqual(mediafile.units.count(), num_units)
        self.assertEqual(mediafile.features.count(), num_units)
        self.assertEqual(mediafile.samplerate, samplerate)
        self.assertEqual(mediafile.channels, num_channels)
        self.assertEqual(mediafile.path, path)
        self.assertEqual(mediafile.duration, duration)

        _duration = 0
        for unit in mediafile.units:
            _duration += unit.duration
        self.assertEqual(_duration, mediafile.duration * mediafile.channels)

    def test_stereo_mediafile(self):
        self._test_file("amen-stereo.wav", 26, 44100, 2, 70560)

    def test_mono_mediafile(self):
        self._test_file("amen-mono.wav", 13, 44100, 1, 70560)


class ClusterUnitsTests(DatabaseTests):

    def test_simple(self):
        add_mediafile(self.session, os.path.join(SOUND_DIR, "amen-mono.wav"),
                      segmentation="beats")
        iterations = cluster_units(self.session, 3)
        self.assertNotEqual(iterations, 0)

        clusters = self.session.query(Features.cluster).all()
        unique = set([])
        for cluster in clusters:
            unique.add(cluster[0])

        self.assertEqual(len(unique), 3)
