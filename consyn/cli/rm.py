# -*- coding: utf-8 -*-
# Copyright (C) 2014, David Poulter
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Remove mediafiles

usage: consyn rm <mediafiles>...

"""
from clint.textui import colored
from clint.textui import puts
import docopt

from ..commands import remove_mediafile
from ..models import MediaFile


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
