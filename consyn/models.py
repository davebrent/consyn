# -*- coding: utf-8 -*-
import os

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import UnicodeText
from sqlalchemy import Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from .settings import FEATURE_SLOTS
from .settings import FEATURE_TYPE


Base = declarative_base()


class Corpus(Base):
    __tablename__ = "corpi"
    id = Column(Integer, primary_key=True)
    path = Column(UnicodeText(255), nullable=False, unique=True, index=True)
    channels = Column(Integer, nullable=False)
    samplerate = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)

    units = relationship("Unit", backref="corpus")
    features = relationship("Features", backref="corpus")

    @property
    def name(self):
        name, _ = os.path.splitext(os.path.basename(self.path))
        return name


class Unit(Base):
    __tablename__ = "units"
    id = Column(Integer, primary_key=True)
    corpus_id = Column(Integer, ForeignKey("corpi.id"))
    channel = Column(Integer, nullable=False)
    position = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)
    features = relationship("Features", uselist=False, backref="unit")


class Features(Base):
    __table__ = Table(
        "features", Base.metadata,
        Column("id", Integer, primary_key=True),
        Column("unit_id", Integer, ForeignKey("units.id")),
        Column("corpus_id", Integer, ForeignKey("corpi.id")),
        *list((Column("feat_{}".format(feature), FEATURE_TYPE, nullable=True,
               default=0)
              for feature in range(FEATURE_SLOTS))) +
        list((Column("label_{}".format(feature), UnicodeText(32),
              nullable=True)
              for feature in range(FEATURE_SLOTS))))

    def __init__(self, unit, features):
        if unit:
            self.unit = unit
            self.corpus = unit.corpus

        if features:
            assert len(features) <= FEATURE_SLOTS
            for index, (label, feature) in enumerate(features.items()):
                setattr(self, "label_{}".format(index), label)
                setattr(self, "feat_{}".format(index), feature)

    def __getitem__(self, name):
        for index in range(FEATURE_SLOTS):
            label = getattr(self, "label_{}".format(index))
            if label == name:
                return getattr(self, "feat_{}".format(index))
        raise Exception("{} not found".format(name))

    def __iter__(self):
        for index in range(FEATURE_SLOTS):
            yield (getattr(self, "label_{}".format(index)),
                   getattr(self, "feat_{}".format(index)))
