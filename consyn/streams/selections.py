# -*- coding: utf-8 -*-
from sqlalchemy.sql import func

from .base import SelectionStream
from ..models import Features
from ..settings import FEATURE_SLOTS


__all__ = [
    "ManhattenDistanceSelection",
]


class ManhattenDistanceSelection(SelectionStream):

    def select(self, unit):
        target_features = unit.features

        dist_func = func.abs(Features.feat_0 - target_features.feat_0)

        for slot in range(FEATURE_SLOTS - 1):
            col_name = "feat_{}".format(slot + 1)
            dist_func += func.abs(getattr(Features, col_name) -
                                  getattr(target_features, col_name))

        feature = self.session.query(Features) \
            .filter(Features.corpus_id.in_(self.corpi)) \
            .order_by(dist_func).limit(1).one()

        return feature.unit
