# -*- coding: utf-8 -*-
"""Remove mediafiles

usage: consyn remove <mediafiles>...

"""
import docopt
from clint.textui import colored
from clint.textui import puts

from ..models import MediaFile
from ..commands import remove_mediafile


def command(session, argv=None):
    args = docopt.docopt(__doc__, argv=argv)
    mediafiles = args["<mediafiles>"]

    if len(mediafiles) == 1 and mediafiles[0] == "all":
        mediafiles = [mediafile.id
                      for mediafile in session.query(MediaFile).all()]

    for param in mediafiles:
        mediafile = MediaFile.by_id_or_name(session, param)
        if not mediafile:
            puts(colored.red("MediaFile {} not found".format(param)))
            continue

        remove_mediafile(session, mediafile)
