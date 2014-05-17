# -*- coding: utf-8 -*-
"""Show onsets and features for a file

usage: consyn show <input> [options]

options:
   -f --framesize <framesize>   Framesize used to read samples [default: 2048].

"""
import collections
import docopt
import numpy
import matplotlib.pyplot as plt

from ..utils import UnitGenerator
from ..utils import MediaFileSampleBuilder
from ..loaders import AubioUnitLoader
from ..models import MediaFile


TICK_COLOR = "#b9b9b9"
GRID_COLOR = "#003902"
WAVE_COLOR = "#00e399"
ONSET_COLOR = "#d20000"
FIGURE_COLOR = "#373737"
BACK_COLOR = "#000000"


def samps_to_secs(samples, samplerate):
    return float(samples) / samplerate


def command(session, argv=None):
    args = docopt.docopt(__doc__, argv=argv)

    mediafile = MediaFile.by_id_or_name(session, args["<input>"])

    results = [{"mediafile": mediafile}] \
        >> UnitGenerator(session) \
        >> AubioUnitLoader(
            hopsize=int(args["--framesize"]),
            key=lambda state: state["unit"].mediafile.path) \
        >> MediaFileSampleBuilder() \
        >> list

    results = results[0]

    duration = float(results["buffer"].shape[1])
    time = numpy.linspace(0, samps_to_secs(duration, mediafile.samplerate),
                          num=duration)

    figure, axes = plt.subplots(mediafile.channels, sharex=True, sharey=True)

    if not isinstance(axes, collections.Iterable):
        axes = [axes]

    for index, ax in enumerate(axes):
        ax.grid(True, color=GRID_COLOR, linestyle='solid')
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
    plt.xlim([0, samps_to_secs(duration, mediafile.samplerate)])
    plt.ylim([-1, 1])
    plt.show()
