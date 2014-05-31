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
import click
from clint.textui import colored
from clint.textui import puts

from . import configurator
from ..commands import remove_mediafile
from ..models import MediaFile


@click.command("rm", short_help="Remove mediafles from a database.")
@click.argument("files", nargs=-1)
@configurator
def command(config, files):
    if len(files) == 1 and files[0] == "all":
        files = [mediafile.id for mediafile in
                 config.session.query(MediaFile).all()]

    for param in files:
        mediafile = MediaFile.by_id_or_name(config.session, param)
        if not mediafile:
            puts(colored.red("MediaFile {} not found".format(param)))
            continue

        remove_mediafile(config.session, mediafile)
