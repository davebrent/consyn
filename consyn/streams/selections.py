from sqlalchemy.sql import func
from .import Stream
from ..models import Features
from ..settings import FEATURE_SLOTS


__all__ = [
    "UnitSelectionStream",
    "ManhattenDistanceSelection",
]


class UnitSelectionStream(Stream):

    def __init__(self, session, corpi):
        super(UnitSelectionStream, self).__init__()
        self.corpi = [corpus.id for corpus in corpi]
        self.session = session

    def __call__(self, pipe):
        for pool in pipe:
            unit = self.select(pool["unit"])
            pool["target"] = pool["unit"]
            pool["unit"] = unit
            yield pool

    def select(self, unit):
        raise NotImplementedError("UnitSelectionStream must implement this")


class ManhattenDistanceSelection(UnitSelectionStream):

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
