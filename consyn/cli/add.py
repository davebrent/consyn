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
import datetime
import os
import time

import click
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

    duration = 0
    failures = []
    succeses = []
    files = set(files)
    start = time.time()
    label = "Adding {} files".format(len(files))

    with click.progressbar(files, label=label) as files:
        for path in files:
            if not os.path.isfile(path):
                failures.append("File does not exist {}".format(path))
                continue

            exists = MediaFile.by_id_or_name(config.session, path)

            if exists:
                if force:
                    remove_mediafile(config.session, exists)
                else:
                    failures.append("File has already been added".format(path))
                    continue

            try:
                mediafile = add_mediafile(config.session, path,
                                          bufsize=bufsize,
                                          hopsize=hopsize,
                                          method=onset_method,
                                          threshold=onset_threshold)

                duration += mediafile.duration / mediafile.samplerate
                config.session.commit()
                succeses.append(path)
            except StandardError:
                failures.append("Unable to open file")

    if len(succeses) > 0:
        succ_str = "Successfully added {} files, ({}) in {}".format(
            len(succeses), datetime.timedelta(seconds=duration),
            datetime.timedelta(seconds=int(time.time() - start)))

        click.secho(succ_str, fg="green")
        if config.verbose:
            for path in succeses:
                click.secho(path, fg="green")

    if len(failures) > 0:
        fail_str = "Failed to add {} files".format(len(failures))
        click.secho(fail_str, fg="red")
        if config.verbose:
            for path in succeses:
                click.secho(path, fg="red")
