# -*- coding: utf-8 -*-
"""Create an audio mosaic

usage: consyn mosaic <outfile> <target> <corpi>...

options:
   -f, --force              Overwrite file(s) if already exists.
   -b, --bufsize <bufsize>  Buffer size used for analysis in samples.
   -h, --hopsize <hopsize>  Hopsize used for analysis in samples.

"""
import os
import docopt

from .. import models
from .. import tasks
from .. import pipeline


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

    if os.path.isfile(args["<outfile>"]):
        if verbose:
            print "File already exists"
    else:
        target = session.query(models.Corpus) \
            .filter(models.Corpus.id == int(args["<target>"])).one()

        corpi = args["<corpi>"]
        cmd_mosaic(session, args["<outfile>"], target, corpi)
