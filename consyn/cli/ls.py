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

import click

from . import configurator
from ..models import MediaFile


@click.command("ls", short_help="List mediafiles in a database.")
@configurator
def command(config):
    col1 = len(str(config.session.query(MediaFile).count()))
    if col1 < 2:
        col1 = 2

    for _id, path in config.session.query(MediaFile.id, MediaFile.path).all():
        if len(path) > (80 - col1 - 2):
            path = path[0:(77 - col1 - 2)] + "..."
        row = "{0:{col1}} {1}".format(_id, path, col1=col1)
        click.echo(row)
