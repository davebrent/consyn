# -*- coding: utf-8 -*-
import os

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import UnicodeText
from sqlalchemy import Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import relationship

from .settings import FEATURE_SLOTS
from .settings import FEATURE_TYPE


Base = declarative_base()


class Corpus(Base):
    """
    id          -- Unique ID.
    path        -- Absolute path to the file.
    channels    -- The number of audio channels in the file.
    samplerate  -- The samplerate of the audio file.
    duration    -- Duration of the file in samples
    """

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
        if self.path:
            name, _ = os.path.splitext(os.path.basename(self.path))
            return name
        return None

    @classmethod
    def by_id_or_name(cls, session, parameter):
        if parameter.isdigit():
            return session.query(cls).get(int(parameter))
        try:
            return session.query(cls).filter_by(
                path=os.path.abspath(parameter)).one()
        except NoResultFound:
            return None

    def __repr__(self):
        keys = ["id", "name", "duration", "channels", "samplerate"]
        values = ["{}={}".format(key, getattr(self, key)) for key in keys]
        values.append("units={}".format(len(self.units)))
        return "<Corpus({})>".format(", ".join(values))

    def __str__(self):
        return self.__repr__()


class Unit(Base):
    """
    corpus      -- The corpus that this unit is related to.
    channel     -- The channel that the unit belongs to in the corpus
    position    -- The sample position that the unit belongs to in the channel
    duration    -- Duration in samples
    """

    __tablename__ = "units"
    id = Column(Integer, primary_key=True)
    corpus_id = Column(Integer, ForeignKey("corpi.id"))
    channel = Column(Integer, nullable=False)
    position = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)
    features = relationship("Features", uselist=False, backref="unit")

    def __repr__(self):
        keys = ["channel", "position", "duration"]
        values = ["{}={}".format(key, getattr(self, key)) for key in keys]
        values.insert(0, "corpus={}".format(self.corpus.name))
        return "<Unit({})>".format(", ".join(values))

    def __str__(self):
        return self.__repr__()


class Features(Base):
    """
    id          -- Unique identifier for the set of features.
    unit        -- The unit the set of features describes.
    corpus      -- The corpus the set of features is part of.
    feat_*      -- The value of the feature.
    label_*     -- The human readable name of the feature.
    """

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
