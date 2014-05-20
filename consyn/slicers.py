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
"""Classes for slicing a stream of AudioFrames"""
import aubio
import numpy

from .base import AudioFrame
from .base import SegmentationStage
from .base import StageFactory
from .settings import DTYPE


__all__ = ["SlicerFactory"]


class SliceBuffer(object):

    def __init__(self, channel, detector):
        self.channel = channel
        self.detector = detector
        self.buffer = numpy.array([], dtype=DTYPE)
        self.onsets = []
        self.position = 0


class BaseSlicer(SegmentationStage):

    def __init__(self, min_slice_size=8192):
        super(BaseSlicer, self).__init__()
        self.min_slice_size = min_slice_size
        self.samplerate = None
        self.channels = {}

    def observe(self, frame):
        output = None
        self.path = frame.path
        self.samplerate = frame.samplerate

        if frame.channel not in self.channels:
            self.channels[frame.channel] = SliceBuffer(
                frame.channel, self.get_detector())

        _slice = self.channels[frame.channel]
        _slice.position = frame.position + frame.duration
        _slice.buffer = numpy.concatenate((_slice.buffer, frame.samples))

        if _slice.detector(frame.samples):
            position = self.get_onset_position(_slice)
            length = len(_slice.onsets)
            if length == 0 or (position - _slice.onsets[0] >
                               self.min_slice_size):
                _slice.onsets.append(position)
            if len(_slice.onsets) == 2:
                output = self.flush(_slice)

        return output

    def finish(self):
        for channel in self.channels:
            _slice = self.channels[channel]
            _slice.onsets.append(_slice.position)
            frame = self.flush(_slice)
            if frame.duration > 0:
                yield frame

    def get_detector(self):
        raise NotImplementedError()

    def get_onset_position(self, _slice):
        raise NotImplementedError()

    def flush(self, _slice):
        duration = _slice.onsets[1] - _slice.onsets[0]
        samples = _slice.buffer[:duration]
        position = _slice.onsets[0]

        _slice.buffer = _slice.buffer[duration:]
        _slice.onsets = [_slice.onsets[1]]

        frame = AudioFrame()
        frame.samplerate = self.samplerate
        frame.path = self.path
        frame.samples = samples
        frame.channel = _slice.channel
        frame.position = position
        frame.duration = duration
        return frame


class OnsetSlicer(BaseSlicer):
    """Slices a stream of audio frames on their onsets.

    This is a thin wrapper around aubio.onset.

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
                 hopsize=512, min_slice_size=0, silence=-90):
        super(OnsetSlicer, self).__init__(min_slice_size=min_slice_size)
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

    def get_onset_position(self, _slice):
        return _slice.detector.get_last()


class RegularDetector(object):

    def __init__(self, size):
        self.size = size
        self.position = 0
        self.count = 0
        self.started = True

    def __call__(self, samples):
        self.position += samples.shape[0]
        if self.position >= self.size or self.started is True:
            self.started = False
            return True
        return False

    def get_last(self):
        position = self.size * self.count
        self.count += 1
        self.position = 0
        return position


class RegularSlicer(BaseSlicer):
    """Slice a stream of audio frames at regular intervals.

    Kwargs:
      winsize (int): Size of slices in samples

    """
    def __init__(self, winsize=1024):
        super(RegularSlicer, self).__init__(min_slice_size=0)
        self.winsize = winsize

    def get_detector(self):
        return RegularDetector(self.winsize)

    def get_onset_position(self, _slice):
        return _slice.detector.get_last()


class BeatSlicer(BaseSlicer):
    """Slice a stream of audio frames at regular musical intervals.

    Kwargs:
      bpm (int): The number of beats per minute in the media file.
      interval (str): The musical interval to slice on.

    """
    def __init__(self, bpm=120, interval="1/16"):
        super(BeatSlicer, self).__init__(min_slice_size=0)
        self.bpm = bpm
        self.interval = interval

    def get_detector(self):
        assert getattr(self, "samplerate") is not None
        winsize = self.get_winsize(self.bpm, self.interval, self.samplerate)
        return RegularDetector(winsize)

    def get_winsize(self, bpm, interval, samplerate):
        if "/" in interval:
            interval = interval.split("/")
            assert len(interval) == 2
            interval = map(float, interval)
            interval = interval[0] / interval[1]
        else:
            interval = float(interval)

        seconds = ((float(60) / float(bpm)) * 4) * interval
        return int(round(seconds * samplerate))

    def get_onset_position(self, _slice):
        return _slice.detector.get_last()


class SlicerFactory(StageFactory):
    objects = {
        "regular": RegularSlicer,
        "onsets": OnsetSlicer,
        "beats": BeatSlicer
    }
