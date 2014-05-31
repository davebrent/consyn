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
import os

import click
from clint.textui import colored
from clint.textui import progress
from clint.textui import puts
from sqlalchemy import not_

from . import configurator
from ..commands import get_mediafile
from ..loaders import AubioUnitLoader
from ..models import MediaFile
from ..resynthesis import Envelope
from ..resynthesis import TimeStretch
from ..selections import NearestNeighbour
from ..utils import AubioWriter
from ..utils import Concatenate
from ..utils import UnitGenerator


class ProgressBar(object):

    def __init__(self, size):
        self.progress_bar = progress.bar(range(size))

    def __call__(self, pipe):
        for pool in pipe:
            self.progress_bar.next()
            yield pool
        self.progress_bar.next()


def cmd_mosaic(session, outfile, target, mediafiles):
    [{"mediafile": target.path, "out": outfile}] \
        >> UnitGenerator(session) \
        >> NearestNeighbour(session, mediafiles) \
        >> AubioUnitLoader(
            hopsize=2048,
            key=lambda state: state["unit"].mediafile.path) \
        >> TimeStretch() \
        >> Envelope() \
        >> ProgressBar(len(target.units)) \
        >> Concatenate(unit_key="target") \
        >> AubioWriter() \
        >> list

    return True


@click.command("mosaic", short_help="Create an audio mosaic.")
@click.option("--force", is_flag=True, default=False,
              help="Overwrite file(s) if already exists.")
@click.argument("output")
@click.argument("target")
@click.argument("mediafiles", nargs=-1)
@configurator
def command(config, output, target, mediafiles, force):
    if os.path.isfile(output) and not force:
        puts(colored.red("File already exists"))
    else:
        target = get_mediafile(config.session, target)
        mediafiles = [get_mediafile(config.session, mediafile)
                      for mediafile in mediafiles]
        config.session.commit()

        if len(mediafiles) == 0:
            mediafiles = config.session.query(MediaFile).filter(not_(
                MediaFile.id == target.id)).all()

        cmd_mosaic(config.session, output, target, mediafiles)
