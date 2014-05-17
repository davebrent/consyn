# -*- coding: utf-8 -*-
"""List files already added

usage: consyn ls

"""
import os

from clint.textui import colored
from clint.textui import puts

from ..models import MediaFile


def command(session, paths=None, verbose=True, force=False):
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
