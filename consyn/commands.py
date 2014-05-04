# -*- coding: utf-8 -*-
import logging
import os
import time

from . import settings
from . import streams
from . import models


__all__ = [
    "add_corpus",
    "get_corpus",
    "remove_corpus"
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
def add_corpus(session, path, bufsize=settings.BUFSIZE,
               hopsize=settings.HOPSIZE, minsize=settings.BUFSIZE,
               method="default", threshold=0):
    """Add a soundfile to the database.

    session     -- Database session
    path        -- Path to the audiofile, can be relative or absolute.
    bufsize     -- Buffersize to use for reading and analysis.
    hopsize     -- Hop size to use for analysis.
    minsize     -- Minimum size of a unit.
    method      -- The method to use for onset detection
    threshold   -- The threshold to use for onset detection
    """

    results = [streams.Pool({"path": path})] \
        >> streams.AubioFrameLoader(bufsize=bufsize, hopsize=hopsize) \
        >> streams.SlicerFactory(
            "onsets",
            winsize=bufsize,
            min_slice_size=minsize,
            method=method,
            threshold=threshold) \
        >> streams.SampleAnalyser(winsize=bufsize, hopsize=hopsize)

    corpus = models.Corpus(duration=0, channels=1)

    for index, result in enumerate(results):
        frame = result["frame"]

        if index == 0:
            corpus.path = os.path.abspath(frame.path)
            corpus.samplerate = frame.samplerate

        if frame.channel == 0:
            corpus.duration += frame.duration

        if frame.channel + 1 > corpus.channels:
            corpus.channels = frame.channel + 1

        unit = models.Unit(corpus=corpus,
                           channel=frame.channel,
                           position=frame.position,
                           duration=frame.duration)

        unit.features = models.Features(unit, result["features"])
        session.add(unit)

    session.add(corpus)
    return corpus


@command
def get_corpus(session, parameter):
    """Retrieve a corpus, adding it with default settings, if it has not been
    seen before.

    session     -- Database session
    parameter   -- A corpus ID or a filepath
    """

    corpus = models.Corpus.by_id_or_name(session, parameter)
    if not corpus:
        corpus = add_corpus(session, parameter)
    return corpus


@command
def remove_corpus(session, corpus):
    """Remove a corpus and all records related to it.

    session     -- Database session
    corpus      -- A corpus object, ID or a filepath
    """

    if not isinstance(corpus, models.Corpus):
        corpus = models.Corpus.by_id_or_name(session, corpus)

    for feature in corpus.features:
        session.delete(feature)

    for unit in corpus.units:
        session.delete(unit)

    session.delete(corpus)
    session.commit()
