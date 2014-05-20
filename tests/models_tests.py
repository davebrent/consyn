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
import unittest
from consyn.models import Features
from consyn import settings


class FeaturesTests(unittest.TestCase):

    def test_init_features(self):
        features = Features(False, {
            "feat_1": 0.1,
            "feat_2": 0.2,
            "feat_3": 0.3
        })

        self.assertEqual(features["feat_1"], 0.1)
        self.assertEqual(features["feat_2"], 0.2)
        self.assertEqual(features["feat_3"], 0.3)

    def test_to_many_features(self):
        feats = {}
        for index in range(settings.FEATURE_SLOTS + 1):
            feats["test_{}".format(index)] = index
        self.assertRaises(AssertionError, Features, False, feats)
