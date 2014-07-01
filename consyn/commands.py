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
import logging
import math
import os
import random
import time

from sqlalchemy.sql import func

from . import settings
from .base import Pipeline
from .ext import Analyser
from .ext import FileLoader
from .models import Features
from .models import MediaFile
from .models import Unit
from .settings import FEATURE_SLOTS
from .slicers import slicer


__all__ = [
    "add_mediafile",
    "get_mediafile",
    "remove_mediafile",
    "cluster_units"
]


logger = logging.getLogger(__name__)
config = settings.get_settings(__name__, name="add_mediafile")


def command(fn):
    def wrapped(*args, **kwargs):
        start = time.time()
        logger.debug("{} started".format(fn.__name__))
        result = fn(*args, **kwargs)
        end = time.time()
        logger.debug("{} completed in {} secs".format(
            fn.__name__, end - start))
        return result
    return wrapped


@command
def add_mediafile(session, path, bufsize=int(config.get("bufsize")),
                  hopsize=int(config.get("hopsize")),
                  segmentation=config.get("segmentation"),
                  method=config.get("method"),
                  threshold=float(config.get("threshold")),
                  silence=float(config.get("silence"))):
    """Add a mediafile to a database.

    Returns the analysed mediafile segmented into units.

    Kwargs:
      session: Sqlalchemy database session
      path (str): Path to the audiofile, can be relative or absolute.
      bufsize (int): Buffersize to use for reading and analysis.
      hopsize (int): Hop size to use for analysis.
      method (str): The method to use for onset detection
      threshold (float): The threshold to use for onset detection

    """
    pipeline = Pipeline([
        FileLoader(path, hopsize=hopsize),
        slicer(
            segmentation,
            winsize=bufsize,
            hopsize=hopsize,
            method=method,
            threshold=threshold,
            silence=silence),
        Analyser(winsize=bufsize, hopsize=hopsize)
    ])

    results = pipeline.run()
    mediafile = MediaFile(duration=0, channels=1)

    for index, result in enumerate(results):
        frame = result["frame"]

        if index == 0:
            mediafile.path = os.path.abspath(frame.path)
            mediafile.samplerate = frame.samplerate
        if frame.channel == 0:
            mediafile.duration += frame.duration
        if frame.channel + 1 > mediafile.channels:
            mediafile.channels = frame.channel + 1

        unit = Unit(mediafile=mediafile, channel=frame.channel,
                    position=frame.position, duration=frame.duration)
        unit.features = Features(unit, result["features"])
        session.add(unit)

    session.add(mediafile)
    return mediafile


@command
def get_mediafile(session, parameter):
    """Retrieve a mediafile, adding it with default settings, if not present.

    Kwargs:
      session: Sqlalchemy database session
      parameter (int|str): A mediafile ID or a filepath

    """
    mediafile = MediaFile.by_id_or_name(session, parameter)
    if not mediafile:
        mediafile = add_mediafile(session, parameter)
    return mediafile


@command
def remove_mediafile(session, mediafile):
    """Remove a mediafile and all records related to it.

    Kwargs:
      session: Sqlalchemy database session
      mediafile (MediaFile|int|str): A mediafile object, ID or a filepath

    """
    if not isinstance(mediafile, MediaFile):
        mediafile = MediaFile.by_id_or_name(session, mediafile)
    session.query(Features).filter(Features.mediafile == mediafile).delete()
    session.query(Unit).filter(Unit.mediafile == mediafile).delete()
    session.delete(mediafile)
    session.commit()


def _distance_from_center(center, feature):
    summed = 0
    for a, b in zip(center.vector(), feature.vector()):
        summed += (a - b) ** 2.0
    return math.sqrt(summed)


def _update_centers(session, centers):
    for cluster_index, center in enumerate(centers):

        query = []
        for slot in range(FEATURE_SLOTS):
            col_name = "feat_{}".format(slot)
            query.append(func.avg(getattr(Features, col_name)))

        averages = session.query(*query).filter(
            Features.cluster == cluster_index).one()

        for index, value in enumerate(averages):
            col_name = "feat_{}".format(index)
            setattr(center, col_name, value)

    return centers


def _equal_centers(previous, centers):
    result = True
    for features1, features2 in zip(previous, centers):
        for feat1, feat2 in zip(features1, features2):
            if feat1[2] != feat2[2]:
                result = False
                break
        if result is False:
            break
    return result


@command
def cluster_units(session, clusters):
    """Cluster all units. Returns the number of iterations

    Kwargs:
      session: Sqlalchemy database session
      clusters (int): Number of clusters

    """
    num_units = session.query(Unit).count()
    centers = [session.query(Unit).get(pk + 1).features.copy()
               for pk in random.sample(xrange(num_units - 2), clusters)]

    previous = map(lambda center: center.copy(), centers)
    iterations = 0

    while True:
        iterations += 1

        for unit in session.query(Unit).all():
            min_distance = float("inf")

            for cluster_index, center in enumerate(centers):
                distance = _distance_from_center(center, unit.features)
                if distance >= min_distance:
                    continue
                min_distance = distance
                unit.features.cluster = cluster_index

        session.flush()
        centers = _update_centers(session, centers)
        session.flush()

        if _equal_centers(previous, centers):
            break
        else:
            previous = map(lambda center: center.copy(), centers)

    return iterations
