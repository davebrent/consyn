# -*- coding: utf-8 -*-
"""Add files

usage: consyn add <input>... [options]

options:
   -f --force               Overwrite file(s) if already exists.
   -b --bufsize <bufsize>   Buffer size in samples [default: 1024].
   -h --hopsize <hopsize>   Hopsize in samples [default: 512].

"""
import os

from docopt import docopt
from sqlalchemy.orm.exc import NoResultFound
from clint.textui import colored
from clint.textui import puts

from .. import pipeline
from .. import tasks
from .. import models
from .. import settings


def cmd_add(session, path, bufsize=settings.BUFSIZE, hopsize=settings.HOPSIZE,
            method="default", threshold=-70):

    soundfile = tasks.Soundfile(bufsize=bufsize, hopsize=bufsize)

    results = [pipeline.State({"path": path})] \
        >> soundfile \
        >> tasks.IterFrames() \
        >> tasks.SegmentFrames(
            winsize=bufsize,
            hopsize=hopsize,
            method=method,
            threshold=threshold) \
        >> tasks.AnalyseSegments(winsize=bufsize, hopsize=hopsize)

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


def command(session, paths=None, verbose=True, force=False):
    if not paths:
        args = docopt(__doc__)
        paths = args["<input>"]

    for path in set(paths):
        path = os.path.abspath(path)

        if not os.path.isfile(path):
            if verbose:
                puts(colored.red(
                    "Skipping {}, file does not exist".format(path)))
            continue
        try:
            exists = session.query(models.Corpus).filter(
                models.Corpus.path == path).one()
            if verbose:
                puts(colored.red(
                    "Skipping {}, file already added. Use -f to overwrite"
                    .format(exists.name)))
        except NoResultFound:
            corpus = cmd_add(session, path)
            session.commit()
            if verbose:
                puts(colored.green(
                    "Successfully added {}".format(corpus.name)))
