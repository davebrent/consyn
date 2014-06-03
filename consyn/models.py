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

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Table
from sqlalchemy import UnicodeText
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from .settings import FEATURE_SLOTS
from .settings import FEATURE_TYPE


Base = declarative_base()


class MediaFile(Base):
    """A file containing audio samples.

    Attributes:
      id (int): Unique ID.
      path (str): Absolute path to the file.
      channels (int): The number of audio channels in the file.
      samplerate (int): The samplerate of the audio file.
      duration (int): Duration of the file in samples

    """
    __tablename__ = "mediafiles"
    id = Column(Integer, primary_key=True)
    path = Column(UnicodeText(255), nullable=False, unique=True, index=True)
    channels = Column(Integer, nullable=False)
    samplerate = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)

    units = relationship("Unit", backref="mediafile", lazy="dynamic")
    features = relationship("Features", backref="mediafile", lazy="dynamic")

    @property
    def name(self):
        if self.path:
            name, _ = os.path.splitext(os.path.basename(self.path))
            return name
        return None

    @classmethod
    def by_id_or_name(cls, session, parameter):
        if isinstance(parameter, int) or parameter.isdigit():
            return session.query(cls).get(int(parameter))
        try:
            return session.query(cls).filter_by(
                path=os.path.abspath(parameter)).one()
        except NoResultFound:
            return None

    def __repr__(self):
        keys = ["id", "name", "duration", "channels", "samplerate"]
        values = ["{}={}".format(key, getattr(self, key)) for key in keys]
        values.append("units={}".format(self.units.count()))
        return "<MediaFile({})>".format(", ".join(values))

    def __str__(self):
        return self.__repr__()


class Unit(Base):
    """A slice of audio in a mediafile.

    Attributes:
      mediafile (MediaFile): The mediafile that this unit is related to.
      features (Features): Extracted audio features.
      channel (int): The channel that the unit belongs to in the mediafile
      position (int): The sample position that the unit belongs to
      duration (int): Duration in samples

    """
    __tablename__ = "units"
    id = Column(Integer, primary_key=True)
    mediafile_id = Column(Integer, ForeignKey("mediafiles.id"))
    channel = Column(Integer, nullable=False)
    position = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)
    features = relationship("Features", uselist=False, backref="unit")

    def __repr__(self):
        keys = ["id", "channel", "position", "duration"]
        values = ["{}={}".format(key, getattr(self, key)) for key in keys]
        values.insert(0, "mediafile={}".format(self.mediafile.name))
        return "<Unit({})>".format(", ".join(values)).encode('utf-8')

    def __str__(self):
        return self.__repr__()


class Features(Base):
    """The extracted audible characteristics of a unit of sound.

    Attributes:
      id (int): Unique identifier for the set of features.
      unit (Unit): The unit the set of features describes.
      mediafile (MediaFile): The mediafile the set of features is part of.
      feat_* (float): The value of the feature.
      label_* (str): The human readable name of the feature.

    """
    __table__ = Table(
        "features", Base.metadata,
        Column("id", Integer, primary_key=True),
        Column("unit_id", Integer, ForeignKey("units.id")),
        Column("mediafile_id", Integer, ForeignKey("mediafiles.id")),
        Column("cluster", Integer, nullable=True, default=0),
        *list((Column("feat_{}".format(feature), FEATURE_TYPE, nullable=True,
               default=0)
              for feature in range(FEATURE_SLOTS))) +
        list((Column("label_{}".format(feature), UnicodeText(32),
              nullable=True)
              for feature in range(FEATURE_SLOTS))))

    def __init__(self, unit, features):
        if unit:
            self.unit = unit
            self.mediafile = unit.mediafile

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
            yield (index, getattr(self, "label_{}".format(index)),
                   getattr(self, "feat_{}".format(index)))

    def __repr__(self):
        values = []
        for index in range(FEATURE_SLOTS):
            values.append("{}={}".format(
                getattr(self, "label_{}".format(index)),
                getattr(self, "feat_{}".format(index))
            ))
        return "<Features({})>".format(", ".join(values))

    def vector(self):
        return [value for _, _, value in self]

    def copy(self):
        copy = Features(False, False)
        for index, label, feature in self:
            setattr(copy, "label_{}".format(index), label)
            setattr(copy, "feat_{}".format(index), feature)
        return copy
