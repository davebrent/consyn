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
from clint.textui import puts

from . import configurator
from ..models import MediaFile


@click.command("ls", short_help="List mediafiles in a database.")
@configurator
def command(config):
    col1 = len(str(config.session.query(MediaFile).count()))
    if col1 < 2:
        col1 = 2
    col2 = 5
    for mediafile in config.session.query(MediaFile).all():
        places = len(str(len(mediafile.units)))
        if col2 < places:
            col2 = places

    puts("{0:{col1}} {1:{col2}} {2}".format(
         "Id", "Units", "Name", col1=col1, col2=col2))

    for mediafile in config.session.query(MediaFile).all():
        name = mediafile.path
        if len(name) > (80 - col1 - 2 - col2):
            name = name[0:(77 - col1 - 2 - col2)] + "..."
        row = "{0:{col1}} {1:{col2}} {2}".format(
            mediafile.id, len(mediafile.units), name, col1=col1, col2=col2)

        if not os.path.isfile(mediafile.path):
            puts(colored.red(row))
        else:
            puts(colored.green(row))
