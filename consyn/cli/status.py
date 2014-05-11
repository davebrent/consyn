# -*- coding: utf-8 -*-
"""List files already added

usage: consyn status [--detailed]

options:
   -d, --detailed       Overwrite file(s) if already exists.

"""
import os

from docopt import docopt
from clint.textui import colored
from clint.textui import puts

from ..settings import DATABASE_URL
from ..settings import FEATURE_SLOTS
from ..settings import DATABASE_PATH
from ..models import MediaFile
from ..models import Unit


def format_file_size(num):
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


def command(session, paths=None, verbose=True, force=False):
    args = docopt(__doc__)

    if args["--detailed"]:
        puts("-" * 80)
        puts("Database url..: {}".format(DATABASE_URL))
        puts("Database size.: {}".format(format_file_size(
            os.path.getsize(DATABASE_PATH))))
        puts("Feature slots.: {}".format(FEATURE_SLOTS))
        puts("Media files...: {}".format(session.query(MediaFile).count()))
        puts("Units.........: {}".format(session.query(Unit).count()))

    puts("-" * 80)
    col1 = len(str(session.query(MediaFile).count()))
    if col1 < 2:
        col1 = 2
    col2 = 5
    for mediafile in session.query(MediaFile).all():
        places = len(str(len(mediafile.units)))
        if col2 < places:
            col2 = places

    puts("{0:{col1}} {1:{col2}} {2}".format(
        "Id", "Units", "Name", col1=col1, col2=col2))

    for mediafile in session.query(MediaFile).all():
        name = mediafile.path
        if len(name) > (80 - col1 - 2 - col2):
            name = name[0:(77 - col1 - 2 - col2)] + "..."
        row = "{0:{col1}} {1:{col2}} {2}".format(
            mediafile.id, len(mediafile.units), name, col1=col1, col2=col2)

        if not os.path.isfile(mediafile.path):
            puts(colored.red(row))
        else:
            puts(colored.green(row))

    puts("-" * 80)
