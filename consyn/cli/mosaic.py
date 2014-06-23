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
from __future__ import unicode_literals
import os

import click
from sqlalchemy import not_

from . import configurator
from ..base import Pipeline
from ..commands import get_mediafile
from ..concatenators import concatenator
from ..ext import UnitLoader
from ..ext import Writer
from ..models import MediaFile
from ..resynthesis import Envelope
from ..resynthesis import TimeStretch
from ..selections import selection
from ..utils import UnitGenerator


class ProgressBar(object):

    def __init__(self, size):
        self.size = size

    def __call__(self, pipe):
        with click.progressbar(pipe, length=self.size) as prog_pipe:
            for pool in prog_pipe:
                yield pool


@click.command("mosaic", short_help="Create an audio mosaic.")
@click.option("--force", is_flag=True, default=False,
              help="Overwrite file(s) if already exists.")
@click.option("--selection", default="nearest",
              help="Unit selection algorithm")
@click.argument("output")
@click.argument("target")
@click.argument("mediafiles", nargs=-1, required=False)
@configurator
def command(config, output, target, mediafiles, force, selection_type):
    if os.path.isfile(output) and not force:
        click.secho("File already exists", fg="red")
        return

    target = get_mediafile(config.session, target)
    mediafiles = [get_mediafile(config.session, mediafile)
                  for mediafile in mediafiles]
    config.session.commit()

    if len(mediafiles) == 0:
        mediafiles = config.session.query(MediaFile).filter(not_(
            MediaFile.id == target.id)).all()

    pipeline = Pipeline([
        UnitGenerator(target, config.session),
        selection(selection_type, config.session, mediafiles),
        UnitLoader(
            hopsize=2048,
            key=lambda state: state["unit"].mediafile.path),
        TimeStretch(),
        Envelope(),
        ProgressBar(target.units.count()),
        concatenator("clip", target, unit_key="target"),
        Writer(target, output),
        list
    ])

    pipeline.run()
