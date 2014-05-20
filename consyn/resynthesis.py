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
import numpy

from .base import SynthesisStage
from .settings import DTYPE


__all__ = [
    "DurationClipper",
    "Envelope"
]


class DurationClipper(SynthesisStage):

    def process(self, samples, unit, target):
        duration = samples.shape[0]
        tmp = numpy.zeros(target.duration, dtype=DTYPE)

        if duration < target.duration:
            tmp[0:duration] = samples
        elif duration > target.duration:
            tmp[0:target.duration] = samples[0:target.duration]
        else:
            tmp = samples

        return tmp, unit


class Envelope(SynthesisStage):

    def process(self, samples, unit, target):
        duration = samples.shape[0]
        envelope = numpy.linspace(1.0, 0.0, num=duration)
        samples *= envelope
        return samples, unit
