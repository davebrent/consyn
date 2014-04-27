# -*- coding: utf-8 -*-
import aubio
import numpy

from ..models import Corpus
from ..settings import DTYPE


__all__ = [
    "Stream",
    "Pool",
    "Soundfile",
    "FrameSampleReader",
    "UnitGenerator",
    "UnitSampleReader",
    "CorpusSampleBuilder",
    "CorpusWriter"
]


class Stream(object):

    def __init__(self, iterable=None):
        self.iterator = iter(iterable if iterable else [])

    def __iter__(self):
        return self.iterator

    def next(self):
        return next(self.iterator)

    def __pipe__(self, inpipe):
        self.iterator = self.__call__(inpipe)
        return self

    @staticmethod
    def pipe(inpipe, outpipe):
        if hasattr(outpipe, '__pipe__'):
            return outpipe.__pipe__(inpipe)
        elif hasattr(outpipe, '__call__'):
            return outpipe(inpipe)

    def __rshift__(self, outpipe):
        return Stream.pipe(self, outpipe)

    def __rrshift__(self, inpipe):
        return Stream.pipe(inpipe, self)


class Pool(object):

    def __init__(self, initial={}):
        self.values = initial

    def __getattr__(self, name):
        return self.values[name]

    def __getitem__(self, name):
        return self.values[name]

    def __setitem__(self, name, value):
        self.values[name] = value

    def values(self):
        return self.values

    def __delitem__(self, name):
        del self.values[name]

    def __str__(self):
        return self.values.__str__()


class Soundfile(Stream):

    def __init__(self, bufsize=1024, hopsize=512,
                 key=lambda state: state["path"]):
        super(Soundfile, self).__init__()
        self.bufsize = bufsize
        self.hopsize = hopsize
        self.key = key
        self.soundfiles = {}

    def __call__(self, pipe):
        for state in pipe:
            path = self.key(state)

            if path not in self.soundfiles:
                self.soundfiles[path] = aubio.source(path, 0, self.bufsize)

            state["soundfile"] = self.soundfiles[path]
            yield state

    def close(self):
        paths = list(self.soundfiles.keys())
        for path in paths:
            self.soundfiles[path].close()
            del self.soundfiles[path]


class FrameSampleReader(Stream):

    def __call__(self, pipe):
        for state in pipe:
            index = 0
            positions = {}
            soundfile = state["soundfile"]
            soundfile.seek(0)

            while True:
                channels, read = soundfile.do_multi()

                for channel, samples in enumerate(channels):
                    if channel not in positions:
                        positions[channel] = 0

                    state["samplerate"] = state["soundfile"].samplerate
                    state["position"] = positions[channel]
                    state["channel"] = channel
                    state["samples"] = samples
                    state["samples_read"] = read
                    state["index"] = index

                    positions[channel] += read
                    yield state

                index += 1
                if read < state["soundfile"].hop_size:
                    break

            state.soundfile.close()


class UnitGenerator(Stream):

    def __init__(self, session):
        super(UnitGenerator, self).__init__()
        self.session = session

    def __call__(self, pipe):
        for state in pipe:
            if not isinstance(state["corpus"], Corpus):
                state["corpus"] = Corpus.by_id_or_name(
                    self.session, state["corpus"])

            for unit in state["corpus"].units:
                state["unit"] = unit
                yield state


class UnitSampleReader(Stream):

    def __call__(self, pipe):
        for state in pipe:
            unit = state["unit"]
            soundfile = state["soundfile"]

            position = 0
            buff = numpy.zeros(unit.duration, dtype=DTYPE)
            soundfile.seek(unit.position)

            while True:
                channels, read = soundfile.do_multi()
                samples = channels[unit.channel]

                if read + position > unit.duration:
                    read = unit.duration - position

                buff[position:position + read] = samples[:read]
                position += read

                if position >= unit.duration:
                    break

            state["samples"] = buff
            yield state


class CorpusSampleBuilder(Stream):

    def __init__(self, channels=2):
        super(CorpusSampleBuilder, self).__init__()
        self.channels = channels
        self.buffers = {}
        self.counts = {}
        self.end = {}

    def __call__(self, pipe):
        for state in pipe:
            corpus = state["corpus"]
            unit = state["unit"]
            samples = state["samples"]

            if corpus.path in self.end:
                continue

            if corpus.path not in self.buffers:
                self.buffers[corpus.path] = numpy.zeros(
                    (corpus.channels, corpus.duration),
                    dtype=DTYPE)
            if corpus.path not in self.counts:
                self.counts[corpus.path] = 0

            buff = self.buffers[corpus.path]

            buff[unit.channel][
                unit.position:unit.position + unit.duration] = samples
            self.counts[corpus.path] += 1

            if self.counts[corpus.path] == len(corpus.units) and \
                    corpus.path not in self.end:
                self.end[corpus.path] = True

                new_state = Pool(initial={
                    "corpus": state["corpus"],
                    "buffer": buff
                })

                if state.values.get("out"):
                    new_state["out"] = state["out"]

                yield new_state


class CorpusWriter(Stream):

    def __call__(self, pipe):
        for state in pipe:
            framesize = 1024
            corpus = state["corpus"]
            buff = state["buffer"]
            outfile = state["out"]

            sink = aubio.sink(outfile, 0, corpus.channels)
            out_samples = numpy.array_split(buff, framesize, axis=1)

            for frame in out_samples:
                amount = frame[0].shape[0]
                sink.do_multi(frame, amount)

            sink.close()
            del sink

            yield Pool(initial={"out": state["out"]})
