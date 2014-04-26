# -*- coding: utf-8 -*-
"""Create an audio mosaic

usage: consyn mosaic <outfile> <target> <corpi>...

options:
   -f, --force              Overwrite file(s) if already exists.

"""
import os
import docopt

from clint.textui import colored
from clint.textui import puts

from .. import tasks
from .. import pipeline
from .. import commands


def cmd_mosaic(session, outfile, target, corpi):
    soundfile = tasks.Soundfile(
        bufsize=2048,
        hopsize=2048,
        key=lambda state: state["unit"].corpus.path)

    [pipeline.State({"corpus": target.path, "out": outfile})] \
        >> tasks.UnitGenerator(session) \
        >> tasks.ManhattenUnitSearcher(session, corpi) \
        >> soundfile \
        >> tasks.UnitSampleReader() \
        >> tasks.UnitSampleClipper() \
        >> tasks.CorpusSampleBuilder() \
        >> tasks.CorpusWriter() \
        >> list

    soundfile.close()
    return True


def command(session, verbose=True, force=False):
    args = docopt.docopt(__doc__)

    if os.path.isfile(args["<outfile>"]) and not args["--force"]:
        puts(colored.red("File already exists"))
    else:
        target = commands.get_or_add_corpus(session, args["<target>"])
        corpi = [commands.get_or_add_corpus(session, corpus)
                 for corpus in args["<corpi>"]]

        session.commit()
        cmd_mosaic(session, args["<outfile>"], target, corpi)
