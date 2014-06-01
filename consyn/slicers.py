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
from __future__ import unicode_literals

import aubio
import numpy

from .base import AudioFrame
from .base import SegmentationStage
from .base import StageFactory
from .settings import DTYPE


__all__ = ["SlicerFactory"]


class Segmentor(object):

    def __init__(self, channel, detector):
        self.channel = channel
        self.detector = detector
        self.buffer = numpy.array([], dtype=DTYPE)
        self.onsets = []
        self.position = 0

    def __repr__(self):
        keys = ['position', 'onsets', 'channel']
        values = ["{}={}".format(key, getattr(self, key)) for key in keys
                  if hasattr(self, key)]
        values.append("buffer={}".format(self.buffer.shape[0]))
        return "<Segmentor({})>".format(", ".join(values))


class BaseSlicer(SegmentationStage):

    def __init__(self):
        super(BaseSlicer, self).__init__()
        self.samplerate = None
        self.channels = {}

    def observe(self, frame):
        output = None
        self.path = frame.path
        self.samplerate = frame.samplerate

        if frame.channel not in self.channels:
            self.channels[frame.channel] = Segmentor(
                frame.channel, self.get_detector())

        segment = self.channels[frame.channel]
        segment.position = frame.position + frame.duration
        segment.buffer = numpy.concatenate((segment.buffer, frame.samples))

        if segment.detector(frame.samples):
            position = self.get_onset_position(segment)
            segment.onsets.append(position)
            if len(segment.onsets) == 2:
                output = self.flush(segment)
        elif frame.position == 0:
            segment.onsets.append(0)

        return output

    def finish(self):
        for channel in self.channels:
            segment = self.channels[channel]

            if len(segment.onsets) == 0:
                segment.onsets.append(segment.position)

            samples = segment.buffer
            duration = samples.shape[0]
            position = segment.onsets[0]

            frame = AudioFrame()
            frame.samplerate = self.samplerate
            frame.path = self.path
            frame.samples = samples
            frame.channel = segment.channel
            frame.position = position
            frame.duration = duration
            yield frame

    def get_detector(self):
        raise NotImplementedError()

    def get_onset_position(self, segment):
        raise NotImplementedError()

    def flush(self, segment):
        duration = segment.onsets[1] - segment.onsets[0]
        samples = segment.buffer[:duration]
        position = segment.onsets[0]

        segment.buffer = segment.buffer[duration:]
        segment.onsets = [segment.onsets[1]]

        frame = AudioFrame()
        frame.samplerate = self.samplerate
        frame.path = self.path
        frame.samples = samples
        frame.channel = segment.channel
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
                 hopsize=512, silence=-90):
        super(OnsetSlicer, self).__init__()
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
        super(RegularSlicer, self).__init__()
        self.winsize = winsize

    def get_detector(self):
        return RegularDetector(self.winsize)

    def get_onset_position(self, segment):
        return segment.detector.get_last()


class BeatSlicer(BaseSlicer):
    """Slice a stream of audio frames at regular musical intervals.

    Kwargs:
      bpm (int): The number of beats per minute in the media file.
      interval (str): The musical interval to slice on.

    """
    def __init__(self, bpm=120, interval="1/16"):
        super(BeatSlicer, self).__init__()
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

    def get_onset_position(self, segment):
        return segment.detector.get_last()


class SlicerFactory(StageFactory):
    objects = {
        "regular": RegularSlicer,
        "onsets": OnsetSlicer,
        "beats": BeatSlicer
    }
