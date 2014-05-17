# -*- coding: utf-8 -*-
import aubio
import numpy

from .base import AudioFrame
from .base import SliceStream
from .base import StreamFactory
from .settings import DTYPE


__all__ = [
    "OnsetSlicer",
    "RegularSlicer",
    "BeatSlicer",
    "SlicerFactory"
]


class SliceBuffer(object):

    def __init__(self, channel, detector):
        self.channel = channel
        self.detector = detector
        self.buffer = numpy.array([], dtype=DTYPE)
        self.onsets = []
        self.position = 0


class BaseSlicer(SliceStream):

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

    def __init__(self, winsize=1024):
        super(RegularSlicer, self).__init__(min_slice_size=0)
        self.winsize = winsize

    def get_detector(self):
        return RegularDetector(self.winsize)

    def get_onset_position(self, _slice):
        return _slice.detector.get_last()


class BeatSlicer(BaseSlicer):

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


class SlicerFactory(StreamFactory):
    objects = {
        "regular": RegularSlicer,
        "onsets": OnsetSlicer,
        "beats": BeatSlicer
    }
