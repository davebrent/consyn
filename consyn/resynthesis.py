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

import numpy

from .base import SynthesisStage


__all__ = [
    "Gain",
    "Envelope",
    "TimeStretch",
    "TrimSilence",
    "SoftClipper"
]


class Gain(SynthesisStage):

    def __init__(self, gain=1.0):
        super(Gain, self).__init__()
        self.gain = float(gain)

    def process(self, samples, unit, target):
        return samples * self.gain, unit


class Envelope(SynthesisStage):

    def __init__(self, fade=30):
        super(Envelope, self).__init__()
        self.fade = fade
        self.attack = numpy.linspace(0.0, 1.0, num=fade)
        self.decay = numpy.linspace(1.0, 0.0, num=fade)

    def process(self, samples, unit, target):
        samples[0:self.fade] *= self.attack
        samples[-self.fade:] *= self.decay
        return samples, unit


class SoftClipper(SynthesisStage):

    def process(self, samples, unit, target):
        samples = numpy.tanh(samples)
        return samples, unit


class TimeStretch(SynthesisStage):

    def __init__(self, factor=None, winsize=1024, overlap=4):
        super(TimeStretch, self).__init__()
        self.factor = factor
        self.winsize = winsize
        self.overlap = overlap

    def process(self, samples, unit, target):
        if self.factor is None:
            if samples.shape[0] == target.duration:
                return samples, unit
            factor = float(target.duration) / float(unit.duration)
        else:
            factor = self.factor

        hopsize = int(float(self.winsize) / float(self.overlap))
        duration = len(samples)

        phi = numpy.zeros(self.winsize)
        out = numpy.zeros(self.winsize, dtype=complex)
        sigout = numpy.zeros(
            int(float(duration) / float(factor) + self.winsize))
        window = numpy.hanning(self.winsize)

        amp = max(samples)
        pos1 = 0
        pos2 = 0

        while pos2 < duration - (self.winsize + hopsize):
            position = int(pos2)

            spec1 = numpy.fft.fft(window * samples[
                position:position + self.winsize])

            spec2 = numpy.fft.fft(window * samples[
                position + hopsize:position + self.winsize + hopsize])

            phi += (numpy.angle(spec2) - numpy.angle(spec1))

            out.real = numpy.cos(phi)
            out.imag = numpy.sin(phi)

            sigout[pos1:pos1 + self.winsize] += (
                window * numpy.fft.ifft(abs(spec2) * out)).real
            pos1 += hopsize
            pos2 += hopsize * factor

        max_samp = max(sigout)

        if max_samp != 0:
            sigout = numpy.array(amp * sigout / max_samp, dtype="float32")
        else:
            sigout = numpy.array(amp * sigout, dtype="float32")

        return sigout, unit


class TrimSilence(SynthesisStage):

    def __init__(self, cutoff=0, trim="fb"):
        self.cutoff = cutoff
        self.trim = trim

    def process(self, samples, unit, target):
        if "f" in self.trim:
            temporary = numpy.empty_like(samples)
            temporary[:] = samples
            temporary[numpy.abs(samples) <= self.cutoff] = 0
            temporary = numpy.trim_zeros(temporary, trim="f")
            samples = samples[samples.shape[0] - temporary.shape[0]:]

        if "b" in self.trim:
            temporary = numpy.empty_like(samples)
            temporary[:] = samples
            temporary[numpy.abs(temporary) <= self.cutoff] = 0
            temporary = numpy.trim_zeros(temporary, trim="b")
            samples = samples[0:temporary.shape[0]]

        return samples, unit
