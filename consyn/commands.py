# -*- coding: utf-8 -*-
import logging
import os
import time

from . import settings
from . import streams
from . import models


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
                  method="default", threshold=0.3):
    """Add a mediafile to the database.

    session     -- Database session
    path        -- Path to the audiofile, can be relative or absolute.
    bufsize     -- Buffersize to use for reading and analysis.
    hopsize     -- Hop size to use for analysis.
    minsize     -- Minimum size of a unit.
    method      -- The method to use for onset detection
    threshold   -- The threshold to use for onset detection
    """

    results = [{"path": path}] \
        >> streams.AubioFrameLoader(hopsize=bufsize) \
        >> streams.SlicerFactory(
            "onsets",
            winsize=bufsize,
            min_slice_size=minsize,
            method=method,
            threshold=threshold) \
        >> streams.SampleAnalyser(winsize=bufsize, hopsize=hopsize)

    mediafile = models.MediaFile(duration=0, channels=1)

    for index, result in enumerate(results):
        frame = result["frame"]

        if index == 0:
            mediafile.path = os.path.abspath(frame.path)
            mediafile.samplerate = frame.samplerate

        if frame.channel == 0:
            mediafile.duration += frame.duration

        if frame.channel + 1 > mediafile.channels:
            mediafile.channels = frame.channel + 1

        unit = models.Unit(mediafile=mediafile,
                           channel=frame.channel,
                           position=frame.position,
                           duration=frame.duration)

        unit.features = models.Features(unit, result["features"])
        session.add(unit)

    session.add(mediafile)
    return mediafile


@command
def get_mediafile(session, parameter):
    """Retrieve a mediafile, adding it with default settings, if it has not
    been seen before.

    session     -- Database session
    parameter   -- A mediafile ID or a filepath
    """

    mediafile = models.MediaFile.by_id_or_name(session, parameter)
    if not mediafile:
        mediafile = add_mediafile(session, parameter)
    return mediafile


@command
def remove_mediafile(session, mediafile):
    """Remove a mediafile and all records related to it.

    session     -- Database session
    mediafile   -- A mediafile object, ID or a filepath
    """

    if not isinstance(mediafile, models.MediaFile):
        mediafile = models.MediaFile.by_id_or_name(session, mediafile)

    for feature in mediafile.features:
        session.delete(feature)

    for unit in mediafile.units:
        session.delete(unit)

    session.delete(mediafile)
    session.commit()
