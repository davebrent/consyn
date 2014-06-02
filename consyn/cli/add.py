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
from clint.textui import colored
from clint.textui import indent
from clint.textui import progress
from clint.textui import puts
try:
    from glob2 import glob
except ImportError:
    from glob import glob

from . import configurator
from ..commands import add_mediafile
from ..commands import remove_mediafile
from ..models import MediaFile


@click.command("add", short_help="Add a mediafile to a database.")
@click.option("--force", is_flag=True, default=False,
              help="Overwrite file(s) if already exists.")
@click.option("--bufsize", default=1024,
              help="Buffer size in samples.")
@click.option("--hopsize", default=512,
              help="Hopsize in samples.")
@click.option("--onset-threshold", default=0.3,
              help="Aubio onset threshold.")
@click.option("--onset-method", default="default",
              help="Aubio onset threshold.")
@click.argument('files', nargs=-1)
@configurator
def command(config, files, force, bufsize, hopsize, onset_threshold,
            onset_method):

    if len(files) == 1 and not os.path.isfile(files[0]):
        files = glob(files[0])

    progress_bar = progress.bar(range(len(files)))
    failures = []
    succeses = []

    for path in set(files):
        if not os.path.isfile(path):
            failures.append("File does not exist {}".format(path))
            progress_bar.next()
            continue

        exists = MediaFile.by_id_or_name(config.session, path)

        if exists:
            if force:
                remove_mediafile(config.session, exists)
            else:
                failures.append("File has already been added".format(path))
                progress_bar.next()
                continue

        add_mediafile(
            config.session, path,
            bufsize=bufsize,
            hopsize=hopsize,
            method=onset_method,
            threshold=onset_threshold)
        config.session.commit()
        succeses.append(path)
        progress_bar.next()

    try:
        progress_bar.next()
    except StopIteration:
        pass

    print("")

    if len(succeses) > 0:
        puts(colored.green("Successfully added {} files".format(
            len(succeses))))
        if config.verbose:
            with indent(2):
                for path in succeses:
                    puts(colored.green(path))

    if len(failures) > 0:
        puts(colored.red("Failed to add {} files".format(
            len(failures))))
        if config.verbose:
            with indent(2):
                for path in succeses:
                    puts(colored.red(path))
