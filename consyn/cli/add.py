# -*- coding: utf-8 -*-
"""Add files

usage: consyn add <input>... [options]

options:
   -v --verbose                   Verbose messages
   -f --force                     Overwrite file(s) if already exists.
   -b --bufsize <bufsize>         Buffer size in samples [default: 1024].
   -h --hopsize <hopsize>         Hopsize in samples [default: 512].
   --minsize <unit-minsize>       Minimum unit size in samples [default: 2048].
   --onset-threshold <threshold>  Aubio onset threshold [default: 0].
   --onset-method <method>        Aubio onset threshold [default: default].

"""
import os

from docopt import docopt
from clint.textui import colored
from clint.textui import puts

from .. import models
from .. import commands


def command(session):
    args = docopt(__doc__)
    paths = args["<input>"]

    for path in set(paths):
        path = os.path.abspath(path)

        if not os.path.isfile(path):
            if args["--verbose"]:
                puts(colored.red(
                    "Skipping {}, file does not exist".format(path)))
            continue

        exists = models.Corpus.by_id_or_name(session, path)
        if exists:
            if args["--force"]:
                commands.remove_corpus(session, exists)
            else:
                if args["--verbose"]:
                    puts(colored.red(
                        "Skipping {}, file already added. Use -f to overwrite"
                        .format(exists.name)))
                continue
        else:
            corpus = commands.add_corpus(
                session, path,
                bufsize=int(args["--bufsize"]),
                hopsize=int(args["--hopsize"]),
                minsize=int(args["--minsize"]),
                method=args["--onset-method"],
                threshold=int(args["--onset-threshold"]))

            session.commit()
            puts(colored.green("Successfully added {}".format(corpus.name)))
