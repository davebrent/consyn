# -*- coding: utf-8 -*-
"""List files already added

usage: consyn status [--detailed]

options:
   -d, --detailed       Overwrite file(s) if already exists.

"""
import os

from docopt import docopt

from ..settings import DATABASE_URL
from ..settings import FEATURE_SLOTS
from ..settings import DATABASE_PATH
from ..models import Corpus
from ..models import Unit


def format_file_size(num):
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


def command(session, paths=None, verbose=True, force=False):
    args = docopt(__doc__)

    if args["--detailed"]:
        print "-" * 80
        print "Database url..: {}".format(DATABASE_URL)
        print "Database size.: {}".format(format_file_size(
            os.path.getsize(DATABASE_PATH)))
        print "Feature slots.: {}".format(FEATURE_SLOTS)
        print "Corpi.........: {}".format(session.query(Corpus).count())
        print "Units.........: {}".format(session.query(Unit).count())

    print "-" * 80
    col1 = len(str(session.query(Corpus).count()))
    if col1 < 2:
        col1 = 2
    col2 = 5
    for corpus in session.query(Corpus).all():
        places = len(str(len(corpus.units)))
        if col2 < places:
            col2 = places

    print("{0:{col1}} {1:{col2}} {2}".format(
        "Id", "Units", "Name", col1=col1, col2=col2))

    for corpus in session.query(Corpus).all():
        name = corpus.path
        if len(name) > (80 - col1 - 2 - col2):
            name = name[0:(77 - col1 - 2 - col2)] + "..."
        print("{0:{col1}} {1:{col2}} {2}".format(
            corpus.id, len(corpus.units), name, col1=col1, col2=col2))

    print "-" * 80
