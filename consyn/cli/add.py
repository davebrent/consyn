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
from clint.textui import indent
from clint.textui import progress
from clint.textui import puts
from sqlalchemy.exc import ProgrammingError

from ..models import MediaFile
from ..commands import add_mediafile
from ..commands import remove_mediafile


def command(session, argv=None):
    args = docopt(__doc__, argv=argv)
    paths = args["<input>"]

    progress_bar = progress.bar(range(len(paths)))
    failures = []
    succeses = []

    try:
        for path in set(paths):
            if not os.path.isfile(path):
                failures.append("File does not exist {}".format(path))
                progress_bar.next()
                continue

            try:
                exists = MediaFile.by_id_or_name(session, path)
            except ProgrammingError:
                # FIXME:
                failures.append("Unicode error {}".format(path))
                progress_bar.next()
                continue

            if exists:
                if args["--force"]:
                    remove_mediafile(session, exists)
                else:
                    failures.append("File has already been added".format(path))
                    progress_bar.next()
                    continue

            add_mediafile(
                session, path,
                bufsize=int(args["--bufsize"]),
                hopsize=int(args["--hopsize"]),
                minsize=int(args["--minsize"]),
                method=args["--onset-method"],
                threshold=int(args["--onset-threshold"]))
            session.commit()
            succeses.append(path)
            progress_bar.next()

        try:
            progress_bar.next()
        except StopIteration:
            pass
    except:
        # TODO: Log errors,
        pass
    finally:
        print("")

        if len(succeses) > 0:
            puts(colored.green("Successfully added {} files".format(
                len(succeses))))
            if args["--verbose"]:
                with indent(2):
                    for path in succeses:
                        puts(colored.green(path))

        if len(failures) > 0:
            puts(colored.red("Failed to add {} files".format(
                len(failures))))
            if args["--verbose"]:
                with indent(2):
                    for path in succeses:
                        puts(colored.red(path))
