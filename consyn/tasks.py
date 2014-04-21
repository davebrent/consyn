# -*- coding: utf-8 -*-
import os

import aubio
import numpy
from sqlalchemy.sql import func

from .models import Corpus
from .models import Features
from .pipeline import Task
from .pipeline import State
from .settings import DTYPE
from .settings import FEATURE_SLOTS


def _slice_array(arr, bufsize=1024, hopsize=512):
    position = 0
    duration = arr.shape[0]
    while True:
        if position + bufsize >= duration:
            yield arr[position:]
            break
        else:
            yield arr[position:position + bufsize]
        position += hopsize


class Soundfile(Task):

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


class IterFrames(Task):

    def __call__(self, pipe):
        for state in pipe:
            index = 0
            position = 0

            while True:
                channels, read = state["soundfile"].do_multi()

                for channel, samples in enumerate(channels):
                    state["samplerate"] = state["soundfile"].samplerate
                    state["position"] = position
                    state["channel"] = channel
                    state["samples"] = samples
                    state["samples_read"] = read
                    state["index"] = index
                    yield state

                index += 1
                position += read

                if read < state["soundfile"].hop_size:
                    break

            state.soundfile.close()


class SegmentFrames(Task):
    # Frames must be in order of there position but may be mixed by channel.

    def __init__(self, winsize=1024, hopsize=512, threshold=-70,
                 method="default", min_slice_size=8192):
        super(SegmentFrames, self).__init__()
        self.winsize = winsize
        self.hopsize = hopsize
        self.threshold = threshold
        self.method = method
        self.min_slice_size = min_slice_size

        self.detectors = {"0": self._detector()}
        self.buffers = {"0": numpy.array([], dtype=DTYPE)}
        self.onsets = {"0": []}

    def _detector(self):
        detector = aubio.onset(self.method, self.winsize, self.hopsize)
        detector.set_threshold(self.threshold)
        return detector

    def __call__(self, pipe):
        for state in pipe:
            channel = state["channel"]

            if channel not in self.detectors:
                self.detectors[channel] = self._detector()
            if channel not in self.buffers:
                self.buffers[channel] = numpy.array([], dtype=DTYPE)
            if channel not in self.onsets:
                self.onsets[channel] = []

            self.buffers[channel] = numpy.concatenate(
                (self.buffers[channel], state["samples"]))

            detector = self.detectors[channel]
            if not detector(state["samples"]):
                continue

            position = detector.get_last()
            length = len(self.onsets[channel])

            if (length == 1 and (position - self.onsets[channel][0]) >
                    self.min_slice_size) or length == 0:
                self.onsets[channel].append(position)

            if length != 2:
                continue

            segment_length = self.onsets[channel][1] - self.onsets[channel][0]
            segment = self.buffers[channel][:segment_length]
            self.buffers[channel] = self.buffers[channel][segment_length:]

            yield State(initial={
                "samplerate": state["samplerate"],
                "path": state["path"],
                "samples": segment,
                "channel": channel,
                "position": self.onsets[channel][0],
                "duration": segment_length
            })

            self.onsets[channel] = [self.onsets[channel][1]]


class AnalyseSegments(Task):

    def __init__(self, samplerate=44100, winsize=1024, hopsize=512, filters=40,
                 coeffs=13):
        super(AnalyseSegments, self).__init__()
        self.winsize = winsize
        self.hopsize = hopsize
        self.descriptors = {}
        self.methods = [
            "default",
            "energy",
            "hfc",
            "complex",
            "phase",
            "specdiff",
            "kl",
            "mkl",
            "specflux",
            "centroid",
            "slope",
            "rolloff",
            "spread",
            "skewness",
            "kurtosis",
            "decrease"]

        for method in self.methods:
            self.descriptors[method] = aubio.specdesc(method, self.winsize)

        self.pvocoder = aubio.pvoc(self.winsize, self.hopsize)
        self.mfcc_feature = aubio.mfcc(winsize, filters, coeffs, samplerate)
        self.mfccs = numpy.zeros([13, ])
        self.coeffs = coeffs
        self.filters = filters

    def __call__(self, pipe):
        for state in pipe:
            features = {}
            frames = _slice_array(state["samples"], bufsize=self.winsize,
                                  hopsize=self.hopsize)
            for frame in frames:
                fftgrain = self.pvocoder(frame)

                mfcc_out = self.mfcc_feature(fftgrain)
                self.mfccs = numpy.vstack((self.mfccs, mfcc_out))

                for method in self.methods:
                    features[method] = self.descriptors[method](fftgrain)[0]

            for method in self.methods:
                features[method] = numpy.mean(features[method])

            mfccs = numpy.mean(self.mfccs, axis=0)
            for index, value in enumerate(list(mfccs)):
                features["mfcc_{}".format(index)] = value

            state["features"] = features
            yield state


class IterCorpi(Task):

    def __init__(self, session):
        super(IterCorpi, self).__init__()
        self.session = session

    def __call__(self, pipe):
        for state in pipe:
            param = state["corpus"]

            if param.isdigit():
                param = int(param)
                corpus = self.session.query(Corpus).get(param)
            else:
                corpus = self.session.query(Corpus).filter(
                    Corpus.path == os.path.abspath(param)).one()

            state["corpus"] = corpus
            for unit in corpus.units:
                state["unit"] = unit
                yield state


class SimilarUnits(Task):
    # uses the manhatten distance

    def __init__(self, session, corpi):
        super(SimilarUnits, self).__init__()
        self.corpi = corpi
        self.session = session

    def __call__(self, pipe):
        for state in pipe:
            target = state["unit"]
            target_features = target.features

            dist_func = func.abs(Features.feat_0 - target_features.feat_0)

            for slot in range(FEATURE_SLOTS - 1):
                col_name = "feat_{}".format(slot + 1)
                dist_func += func.abs(getattr(Features, col_name) -
                                      getattr(target_features, col_name))

            feature = self.session.query(Features) \
                .filter(Features.corpus_id.in_(self.corpi)) \
                .order_by(dist_func).limit(1).one()

            state["target"] = target
            state["unit"] = feature.unit
            yield state


class ReadUnits(Task):

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


class TrimUnits(Task):

    def __call__(self, pipe):
        for state in pipe:
            target = state["target"]
            duration = state["samples"].shape[0]
            tmp = numpy.zeros(target.duration, dtype=DTYPE)

            if duration < target.duration:
                tmp[0:duration] = state["samples"]
            elif duration > target.duration:
                tmp[0:target.duration] = state["samples"][0:target.duration]

            state["unit"].position = target.position
            state["unit"].duration = target.duration
            state["samples"] = tmp
            yield state


class EnvelopeUnits(Task):

    def __call__(self, pipe):
        for state in pipe:
            duration = state["samples"].shape[0]
            envelope = numpy.linspace(1.0, 0.0, num=duration)
            state["samples"] *= envelope
            yield state


class BuildCorpus(Task):

    def __init__(self, channels=2):
        super(BuildCorpus, self).__init__()
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

                yield State(initial={
                    "corpus": state["corpus"],
                    "buffer": buff,
                    "out": state["out"]
                })


class WriteCorpus(Task):

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

            yield State(initial={
                "out": state["out"]
            })
