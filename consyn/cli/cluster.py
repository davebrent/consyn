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

import collections
import math
import random

import click

from . import configurator
from ..models import Unit
from ..models import Features


def initialize_centers(session, num_clusters, num_units):
    return [session.query(Unit).get(pk + 1).features.copy()
            for pk in random.sample(xrange(num_units - 2), num_clusters)]


def distance_from_center(center, feature):
    summed = 0
    for a, b in zip(center.vector(), feature.vector()):
        summed += (a - b) ** 2.0
    return math.sqrt(summed)


def update_centers(session, centers):
    for cluster_index, center in enumerate(centers):
        averages = collections.defaultdict(float)

        all_features = session.query(Features).filter(
            Features.cluster == cluster_index)

        for features in all_features.all():
            for index, label, value in features:
                averages["feat_{}".format(index)] += value

        total = all_features.count()
        for key in averages:
            setattr(center, key, float(averages[key]) / float(total))

    return centers


def equal_centers(previous, centers):
    result = True
    for features1, features2 in zip(previous, centers):
        for feat1, feat2 in zip(features1, features2):
            if feat1[2] != feat2[2]:
                result = False
                break
        if result is False:
            break
    return result


@click.command("cluster", short_help="Cluster units.")
@click.argument("clusters")
@configurator
def command(config, clusters):
    clusters = int(clusters)
    num_units = config.session.query(Unit).count()
    centers = initialize_centers(config.session, clusters, num_units)
    previous = map(lambda center: center.copy(), centers)
    iterations = 0

    while True:
        iterations += 1

        for unit in config.session.query(Unit).all():
            min_distance = float("inf")

            for cluster_index, center in enumerate(centers):
                distance = distance_from_center(center, unit.features)
                if distance >= min_distance:
                    continue
                min_distance = distance
                unit.features.cluster = cluster_index

        config.session.flush()
        centers = update_centers(config.session, centers)
        config.session.flush()

        if equal_centers(previous, centers):
            break
        else:
            previous = map(lambda center: center.copy(), centers)

    click.secho("Clustering completed sucessfully with {} iterations"
                .format(iterations), fg="green")

    if config.verbose:
        for cluster in xrange(clusters):
            total = config.session.query(Features).filter(
                Features.cluster == cluster).count()
            click.echo("Cluster {}: {} units".format(cluster, total))
