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
"""Create an audio mosaic

usage: consyn mosaic <outfile> <target> [<mediafiles>...] [options]

options:
   -f, --force              Overwrite file(s) if already exists.

"""
import os

from clint.textui import colored
from clint.textui import progress
from clint.textui import puts
import docopt
from sqlalchemy import not_

from ..commands import get_mediafile
from ..loaders import AubioUnitLoader
from ..models import MediaFile
from ..resynthesis import DurationClipper
from ..resynthesis import Envelope
from ..selections import NearestNeighbour
from ..utils import Concatenate
from ..utils import AubioWriter
from ..utils import UnitGenerator


class ProgressBar(object):

    def __init__(self, size):
        self.progress_bar = progress.bar(range(size - 1))

    def __call__(self, pipe):
        for pool in pipe:
            self.progress_bar.next()
            yield pool


def cmd_mosaic(session, outfile, target, mediafiles):
    [{"mediafile": target.path, "out": outfile}] \
        >> UnitGenerator(session) \
        >> NearestNeighbour(session, mediafiles) \
        >> AubioUnitLoader(
            hopsize=2048,
            key=lambda state: state["unit"].mediafile.path) \
        >> DurationClipper() \
        >> Envelope() \
        >> ProgressBar(len(target.units)) \
        >> Concatenate(unit_key="target") \
        >> AubioWriter() \
        >> list

    return True


def command(session, argv=None):
    args = docopt.docopt(__doc__, argv=argv)

    if os.path.isfile(args["<outfile>"]) and not args["--force"]:
        puts(colored.red("File already exists"))
    else:
        target = get_mediafile(session, args["<target>"])
        mediafiles = [get_mediafile(session, mediafile)
                      for mediafile in args["<mediafiles>"]]
        session.commit()

        if len(mediafiles) == 0:
            mediafiles = session.query(MediaFile).filter(not_(
                MediaFile.id == target.id)).all()

        cmd_mosaic(session, args["<outfile>"], target, mediafiles)
