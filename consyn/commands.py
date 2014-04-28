# -*- coding: utf-8 -*-
import os

from . import settings
from . import streams
from . import models


def add_corpus(session, path, bufsize=settings.BUFSIZE,
               hopsize=settings.HOPSIZE, minsize=settings.BUFSIZE,
               method="default", threshold=0):

    results = [streams.Pool({"path": path})] \
        >> streams.AubioFrameLoader(bufsize=bufsize, hopsize=hopsize) \
        >> streams.OnsetSlicer(
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


def get_or_add_corpus(session, parameter):
    corpus = models.Corpus.by_id_or_name(session, parameter)
    if not corpus:
        corpus = add_corpus(session, parameter)
    return corpus


def remove_corpus(session, corpus):
    if not isinstance(corpus, models.Corpus):
        corpus = models.Corpus.by_id_or_name(session, corpus)

    for feature in corpus.features:
        session.delete(feature)

    for unit in corpus.units:
        session.delete(unit)

    session.delete(corpus)
    session.commit()
