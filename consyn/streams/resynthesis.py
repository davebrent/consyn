# -*- coding: utf-8 -*-
import numpy

from .base import ResynthesisStream
from ..settings import DTYPE


__all__ = [
    "DurationClipper",
    "EnvelopeUnits"
]


class DurationClipper(ResynthesisStream):

    def process(self, samples, unit, target):
        duration = samples.shape[0]
        tmp = numpy.zeros(target.duration, dtype=DTYPE)

        if duration < target.duration:
            tmp[0:duration] = samples
        elif duration > target.duration:
            tmp[0:target.duration] = samples[0:target.duration]

        return tmp, unit


class EnvelopeUnits(ResynthesisStream):

    def process(self, samples, unit, target):
        duration = samples.shape[0]
        envelope = numpy.linspace(1.0, 0.0, num=duration)
        samples *= envelope
        return samples, unit
