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
from ..models import Features
from ..commands import cluster_units


@click.command("cluster", short_help="Cluster units.")
@click.argument("clusters")
@configurator
def command(config, clusters):
    clusters = int(clusters)
    iterations = cluster_units(config.session, clusters)

    click.secho("Clustering completed sucessfully with {} iterations"
                .format(iterations), fg="green")

    if config.verbose:
        for cluster in xrange(clusters):
            total = config.session.query(Features).filter(
                Features.cluster == cluster).count()
            click.echo("Cluster {}: {} units".format(cluster, total))
