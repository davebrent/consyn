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
"""Unit selection algorithms"""
from __future__ import unicode_literals
import random

from sqlalchemy.sql import func

from .base import SelectionStage
from .models import Features
from .models import Unit
from .settings import FEATURE_SLOTS
from .utils import factory


__all__ = ["selection"]


class NearestNeighbour(SelectionStage):
    """Retrieve the nearest unit using the manhattan distance"""
    def select(self, unit):
        target_features = unit.features

        dist_func = func.abs(Features.feat_0 - target_features.feat_0)

        for slot in range(FEATURE_SLOTS - 1):
            col_name = "feat_{}".format(slot + 1)
            dist_func += func.abs(getattr(Features, col_name) -
                                  getattr(target_features, col_name))

        pk = self.session.query(Features.unit_id) \
            .filter(Features.mediafile_id.in_(self.mediafiles)) \
            .order_by(dist_func).limit(1).one()

        return self.session.query(Unit).get(pk)


class RandomUnit(SelectionStage):

    def select(self, unit):
        count = self.session.query(Unit).count()
        return self.session.query(Unit).get(random.randint(1, count - 1))


def selection(name, *args, **kwargs):
    objects = {"nearest": NearestNeighbour,
               "random": RandomUnit}
    return factory(objects, name, *args, **kwargs)
