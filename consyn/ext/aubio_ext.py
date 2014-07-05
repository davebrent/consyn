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
import logging

import aubio
import numpy

from ..base import AnalysisStage
from ..base import AudioFrame
from ..base import FileLoaderStage
from ..base import Stage
from ..base import UnitLoaderStage
from ..settings import DTYPE
from ..settings import get_settings
from ..slicers import BaseSlicer
from ..utils import slice_array


__all__ = [
    "AubioFileLoader",
    "AubioUnitLoader",
    "AubioAnalyser",
    "AubioOnsetSlicer",
    "AubioWriter"
]


logger = logging.getLogger(__name__)
settings = get_settings(__name__)


class AubioFileCache(object):

    _soundfiles = {}
    _counts = {}

    def open(self, path, hopsize):
        if path not in self._soundfiles:
            soundfile = aubio.source(path.encode("utf-8"), 0, hopsize)
            self._soundfiles[path] = soundfile
            self._counts[path] = 0
        if len(self._soundfiles) > settings.get("max_open_files"):
            minimum = float("inf")
            min_path = None
            for path in self._counts:
                if minimum > self._counts[path]:
                    minimum = self._counts[path]
                    min_path = path
            self._close(min_path)

        self._counts[path] += 1
        return self._soundfiles[path]

    def close(self):
        for path in self._soundfiles.keys():
            self._close(path)

    def _close(self, path):
        self._soundfiles[path].close()
        del self._soundfiles[path]
        del self._counts[path]


class AubioFileLoader(FileLoaderStage, AubioFileCache):

    def read(self, path):
        soundfile = self.open(path, self.hopsize)
        soundfile.seek(0)

        index = 0
        positions = {}

        while True:
            channels, read = soundfile.do_multi()

            if read == 0:
                break

            for channel, samples in enumerate(channels):
                if channel not in positions:
                    positions[channel] = 0

                frame = AudioFrame()
                frame.samplerate = soundfile.samplerate
                frame.position = positions[channel]
                frame.channel = channel
                frame.samples = samples[:read]
                frame.duration = read
                frame.index = index
                frame.path = path

                positions[channel] += read
                yield frame

            index += 1
            if read < soundfile.hop_size:
                break


class AubioUnitLoader(UnitLoaderStage, AubioFileCache):

    def read(self, path, unit):
        soundfile = self.open(path, self.hopsize)
        soundfile.seek(unit.position)

        pos = 0
        buff = numpy.zeros(unit.duration, dtype=DTYPE)

        while True:
            channels, read = soundfile.do_multi()
            samples = channels[unit.channel]

            if read + pos > unit.duration:
                read = unit.duration - pos

            buff[pos:pos + read] = samples[:read]
            pos += read

            if pos >= unit.duration or read == 0:
                break

        frame = AudioFrame()
        frame.samplerate = soundfile.samplerate
        frame.position = unit.position
        frame.channel = unit.channel
        frame.samples = buff
        frame.duration = unit.duration
        frame.index = 0
        frame.path = path

        yield frame


class AubioAnalyser(AnalysisStage):

    def __init__(self, samplerate=44100, winsize=1024, hopsize=512, filters=40,
                 coeffs=13):
        super(AubioAnalyser, self).__init__()
        self.winsize = winsize
        self.hopsize = hopsize
        self.coeffs = coeffs
        self.filters = filters
        self.descriptors = {}
        self.methods = ["default", "energy", "hfc", "complex", "phase",
                        "specdiff", "kl", "mkl", "specflux", "centroid",
                        "slope", "rolloff", "spread", "skewness", "kurtosis",
                        "decrease"]

        for method in self.methods:
            self.descriptors[method] = aubio.specdesc(method, self.winsize)

        self.pvocoder = aubio.pvoc(self.winsize, self.hopsize)
        self.mfcc_feature = aubio.mfcc(winsize, filters, coeffs, samplerate)
        self.mfccs = numpy.zeros([self.coeffs, ])

    def __len__(self):
        return len(self.methods) + self.coeffs

    def analyse(self, frame):
        samples = frame.samples
        features = collections.defaultdict(lambda: 0.0)
        frames = slice_array(samples, bufsize=self.winsize,
                             hopsize=self.hopsize)

        for frame in frames:
            fftgrain = self.pvocoder(frame)

            mfcc_out = self.mfcc_feature(fftgrain)
            self.mfccs = numpy.vstack((self.mfccs, mfcc_out))

            for method in self.methods:
                features[method] += self.descriptors[method](fftgrain)[0]

        if len(features) == 0:
            return None

        for method in self.methods:
            features[method] = numpy.mean(features[method])

        mfccs = numpy.mean(self.mfccs, axis=0)
        for index, value in enumerate(list(mfccs)):
            features["mfcc_{}".format(index)] = value

        return features


class AubioOnsetSlicer(BaseSlicer):
    """Slices a stream of audio frames on their onsets.

    Kwargs:
      winsize (int): The size of the buffer to analyze.
      hopsize (int): The number of samples between two consecutive analysis.
      threshold (float): Set the threshold value for the onset peak picking.
                         Typical values are typically within 0.001 and 0.9
      method (str): Available methods are: default, energy, hfc, complex,
                    phase, specdiff, kl, mkl, specflux.
      silence (float): Set the silence threshold, in dB, under which the pitch
                       will not be detected

    """
    def __init__(self, winsize=1024, threshold=0.3, method="default",
                 hopsize=512, silence=-90):
        super(AubioOnsetSlicer, self).__init__()
        self.winsize = winsize
        self.hopsize = hopsize
        self.threshold = threshold
        self.method = method
        self.silence = silence

    def get_detector(self):
        detector = aubio.onset(self.method, self.winsize, self.hopsize,
                               self.samplerate)
        detector.set_threshold(self.threshold)
        detector.set_silence(self.silence)
        return detector

    def get_onset_position(self, segment):
        return segment.detector.get_last()


class AubioWriter(Stage):

    def __init__(self, mediafile, outfile):
        super(AubioWriter, self).__init__()
        self.outfile = outfile
        self.mediafile = mediafile

    def __call__(self, pipe):
        for pool in pipe:
            framesize = 2048
            buff = pool["buffer"]

            sink = aubio.sink(self.outfile, 0, self.mediafile.channels)
            out_samples = numpy.array_split(
                buff, int(float(self.mediafile.duration) / int(framesize)),
                axis=1)

            for frame in out_samples:
                amount = frame[0].shape[0]
                sink.do_multi(frame, amount)

            sink.close()
            del sink

            yield {"out": self.outfile}
