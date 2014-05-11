# -*- coding: utf-8 -*-
"""Remove mediafiles

usage: consyn remove <mediafiles>...

"""
import docopt
from clint.textui import colored
from clint.textui import puts

from .. import models
from .. import commands


def command(session, paths=None, verbose=True, force=False):
    args = docopt.docopt(__doc__)
    mediafiles = args["<mediafiles>"]

    if len(mediafiles) == 1 and mediafiles[0] == "all":
        mediafiles = [mediafile.id
                      for mediafile in session.query(models.MediaFile).all()]

    for param in mediafiles:
        mediafile = models.MediaFile.by_id_or_name(session, param)
        if not mediafile:
            puts(colored.red("MediaFile {} not found".format(param)))
            continue

        commands.remove_mediafile(session, mediafile)
