# -*- coding: utf-8 -*-
import numpy
from ..settings import DTYPE
from .core import Stream


__all__ = [
    "DurationClipper",
    "EnvelopeUnits"
]


class ResynthesisStream(Stream):

    def __init__(self):
        super(ResynthesisStream, self).__init__()

    def __call__(self, pipe):
        for pool in pipe:
            samples, unit = self.process(
                pool["samples"],
                pool["unit"],
                pool["target"])
            pool["unit"] = unit
            pool["samples"] = samples
            yield pool

    def process(self, samples, unit, target):
        raise NotImplementedError("Resynthesisers must implement this")


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
