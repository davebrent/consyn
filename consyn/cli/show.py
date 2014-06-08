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

import click
import matplotlib.pyplot as plt
import numpy

from . import configurator
from ..base import Pipeline
from ..features import AubioFeatures
from ..loaders import AubioUnitLoader
from ..models import MediaFile
from ..models import Unit
from ..utils import Concatenate
from ..utils import UnitGenerator


FEATURES = AubioFeatures().methods
TICK_COLOR = "#b9b9b9"
GRID_COLOR = "#003902"
WAVE_COLOR = "#00e399"
ONSET_COLOR = "#d20000"
FIGURE_COLOR = "#373737"
BACK_COLOR = "#000000"


def samps_to_secs(samples, samplerate):
    return float(samples) / samplerate


@click.command("show", short_help="Show a mediafile and its onsets.")
@click.option("--hopsize", default=1024,
              help="Hopsize used to read samples.")
@click.argument("mediafile")
@configurator
def command(config, mediafile, hopsize):
    mediafile = MediaFile.by_id_or_name(config.session, mediafile)

    pipeline = Pipeline([
        UnitGenerator(mediafile, config.session),
        AubioUnitLoader(
            hopsize=hopsize,
            key=lambda state: state["unit"].mediafile.path),
        Concatenate(),
        list
    ])

    results = pipeline.run()
    results = results[0]

    duration = float(results["buffer"].shape[1])
    time = numpy.linspace(0, samps_to_secs(duration, mediafile.samplerate),
                          num=duration)

    figure, axes = plt.subplots(
        mediafile.channels, sharex=True, sharey=True,
        subplot_kw={
            "xlim": [0, samps_to_secs(duration, mediafile.samplerate)],
            "ylim": [-1, 1]
        }
    )

    # Features

    figure_feats, axes_feats = plt.subplots(len(FEATURES), sharex=True)
    features_all = collections.defaultdict(list)
    timings = []
    for unit in mediafile.units.order_by(Unit.position) \
            .filter(Unit.channel == 0):
        for feature in FEATURES:
            features_all[feature].append(unit.features[feature])
        timings.append(unit.position)

    for index, key in enumerate(features_all):
        axes_feats[index].plot(timings, features_all[key], color=WAVE_COLOR)
        axes_feats[index].set_axisbelow(True)
        axes_feats[index].patch.set_facecolor(BACK_COLOR)

        for label in axes_feats[index].get_xticklabels():
            label.set_color(TICK_COLOR)
            label.set_fontsize(1)

        for label in axes_feats[index].get_yticklabels():
            label.set_color(TICK_COLOR)
            label.set_fontsize(1)

    # Buffer

    if not isinstance(axes, collections.Iterable):
        axes = [axes]

    for index, ax in enumerate(axes):
        ax.grid(True, color=GRID_COLOR, linestyle="solid")
        ax.set_axisbelow(True)

        for label in ax.get_xticklabels():
            label.set_color(TICK_COLOR)
            label.set_fontsize(9)

        for label in ax.get_yticklabels():
            label.set_color(TICK_COLOR)
            label.set_fontsize(9)

        ax.patch.set_facecolor(BACK_COLOR)

        ax.plot(time, results["buffer"][index], color=WAVE_COLOR)

        for unit in mediafile.units:
            position = samps_to_secs(unit.position, mediafile.samplerate)
            position = position if position != 0 else 0.003

            if unit.channel == index:
                ax.axvline(x=position, color=ONSET_COLOR)

    figure.patch.set_facecolor(FIGURE_COLOR)
    figure.set_tight_layout(True)

    figure_feats.set_facecolor(FIGURE_COLOR)
    figure_feats.set_tight_layout(True)

    plt.show()
