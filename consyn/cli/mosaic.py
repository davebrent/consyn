# -*- coding: utf-8 -*-
"""Create an audio mosaic

usage: consyn mosaic <outfile> <target> [<mediafiles>...] [options]

options:
   -f, --force              Overwrite file(s) if already exists.

"""
import os
import docopt
from clint.textui import colored
from clint.textui import puts
from clint.textui import progress
from sqlalchemy import not_

from .. import streams
from .. import commands
from .. import models


class ProgressBar(object):

    def __init__(self, size):
        self.progress_bar = progress.bar(range(size - 1))

    def __call__(self, pipe):
        for pool in pipe:
            self.progress_bar.next()
            yield pool


def cmd_mosaic(session, outfile, target, mediafiles):
    [{"mediafile": target.path, "out": outfile}] \
        >> streams.UnitGenerator(session) \
        >> streams.ManhattenDistanceSelection(session, mediafiles) \
        >> streams.AubioUnitLoader(
            hopsize=2048,
            key=lambda state: state["unit"].mediafile.path) \
        >> streams.DurationClipper() \
        >> ProgressBar(len(target.units)) \
        >> streams.MediaFileSampleBuilder(unit_key="target") \
        >> streams.MediaFileWriter() \
        >> list

    return True


def command(session, verbose=True, force=False):
    args = docopt.docopt(__doc__)

    if os.path.isfile(args["<outfile>"]) and not args["--force"]:
        puts(colored.red("File already exists"))
    else:
        target = commands.get_mediafile(session, args["<target>"])
        mediafiles = [commands.get_mediafile(session, mediafile)
                      for mediafile in args["<mediafiles>"]]
        session.commit()

        if len(mediafiles) == 0:
            mediafiles = session.query(models.MediaFile).filter(not_(
                models.MediaFile.id == target.id)).all()

        cmd_mosaic(session, args["<outfile>"], target, mediafiles)
