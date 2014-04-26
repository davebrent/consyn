# -*- coding: utf-8 -*-
import os

from . import settings
from . import tasks
from . import pipeline
from . import models


def add_corpus(session, path, bufsize=settings.BUFSIZE,
               hopsize=settings.HOPSIZE, method="default", threshold=-70):

    soundfile = tasks.Soundfile(bufsize=bufsize, hopsize=bufsize)

    results = [pipeline.State({"path": path})] \
        >> soundfile \
        >> tasks.FrameSampleReader() \
        >> tasks.FrameOnsetSlicer(
            winsize=bufsize,
            method=method,
            threshold=threshold) \
        >> tasks.SampleAnalyser(winsize=bufsize, hopsize=hopsize)

    corpus = models.Corpus(duration=0, channels=1)

    for index, result in enumerate(results):
        if index == 0:
            corpus.path = os.path.abspath(result["path"])
            corpus.samplerate = result["samplerate"]

        if result["channel"] == 0:
            corpus.duration += result["duration"]

        if result["channel"] + 1 > corpus.channels:
            corpus.channels = result["channel"] + 1

        unit = models.Unit(corpus=corpus,
                           channel=result["channel"],
                           position=result["position"],
                           duration=result["duration"])

        unit.features = models.Features(unit, result["features"])
        session.add(unit)

    session.add(corpus)
    soundfile.close()
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
