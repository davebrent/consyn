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
"""Common commands operating on mediafiles"""
import logging
import os
import time

from . import settings
from .features import AubioFeatures
from .loaders import AubioFileLoader
from .models import Features
from .models import MediaFile
from .models import Unit
from .slicers import SlicerFactory


__all__ = [
    "add_mediafile",
    "get_mediafile",
    "remove_mediafile"
]


logger = logging.getLogger(__name__)


def command(fn):
    def wrapped(*args, **kwargs):
        start = time.time()
        logger.debug("{} started args={}, kwargs={}".format(
            fn.__name__, args, kwargs))
        result = fn(*args, **kwargs)
        end = time.time()
        logger.debug("{} completed in {} secs".format(
            fn.__name__, end - start))
        return result
    return wrapped


@command
def add_mediafile(session, path, bufsize=settings.BUFSIZE,
                  hopsize=settings.HOPSIZE, minsize=settings.BUFSIZE,
                  method="default", threshold=0.3, silence=-90):
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
    results = [{"path": path}] \
        >> AubioFileLoader(hopsize=hopsize) \
        >> SlicerFactory(
            "onsets",
            winsize=bufsize,
            hopsize=hopsize,
            method=method,
            threshold=threshold,
            silence=-90) \
        >> AubioFeatures(winsize=bufsize, hopsize=hopsize)

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
    for feature in mediafile.features:
        session.delete(feature)
    for unit in mediafile.units:
        session.delete(unit)

    session.delete(mediafile)
    session.commit()
