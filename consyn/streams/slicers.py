import aubio
import numpy
import collections

from ..settings import DTYPE
from .core import Stream
from .core import Pool


__all__ = [
    "OnsetSlicer"
]


class SliceStream(Stream):
    # Frames must be in order of there position but may be mixed by channel.
    def __init__(self):
        super(SliceStream, self).__init__()

    def __call__(self, pipe):
        for pool in pipe:
            _slice = self.observe(
                pool["samples"], pool["samples_read"],
                pool["position"], pool["channel"],
                pool["samplerate"], pool["path"])
            if _slice is None:
                continue
            yield Pool(initial=_slice)

        closing = self.finish()
        if isinstance(closing, collections.Iterable):
            for _slice in closing:
                yield Pool(initial=_slice)

    def observe(self, samples, read, position, channel, samplerate, path):
        raise NotImplementedError("SliceStream must implement this")

    def finish(self, samples, path, channel, samplerate):
        pass


class OnsetSlicer(SliceStream):

    def __init__(self, winsize=1024, threshold=-70, method="default",
                 min_slice_size=8192):
        super(OnsetSlicer, self).__init__()
        self.winsize = winsize
        self.hopsize = winsize
        self.threshold = threshold
        self.method = method
        self.min_slice_size = min_slice_size

        self.detectors = {}
        self.buffers = {0: numpy.array([], dtype=DTYPE)}
        self.onsets = {0: []}
        self.positions = {0: 0}

    def observe(self, samples, read, position, channel, samplerate, path):
        output = None
        self.path = path
        self.samplerate = samplerate

        if channel not in self.detectors:
            self.detectors[channel] = self._detector()
            self.buffers[channel] = numpy.array([], dtype=DTYPE)
            self.onsets[channel] = []
            self.positions[channel] = 0

        self.positions[channel] = position + read
        self.buffers[channel] = numpy.concatenate(
            (self.buffers[channel], samples))

        detector = self.detectors[channel]
        if detector(samples):
            position = detector.get_last()
            length = len(self.onsets[channel])
            if length == 0 or (position - self.onsets[channel][0] >
                               self.min_slice_size):
                self.onsets[channel].append(position)
            if len(self.onsets[channel]) == 2:
                output = self._flush(channel, self.path, self.samplerate)

        return output

    def finish(self):
        for channel in self.onsets:
            self.onsets[channel].append(self.positions[channel])
            yield self._flush(channel, self.path, self.samplerate)

    def _detector(self):
        detector = aubio.onset(self.method, self.winsize, self.hopsize)
        detector.set_threshold(self.threshold)
        return detector

    def _flush(self, channel, path, samplerate):
        segment_length = self.onsets[channel][1] - self.onsets[channel][0]
        segment = self.buffers[channel][:segment_length]
        self.buffers[channel] = self.buffers[channel][segment_length:]

        position = self.onsets[channel][0]
        self.onsets[channel] = [self.onsets[channel][1]]

        return {
            "samplerate": samplerate,
            "path": path,
            "samples": segment,
            "channel": channel,
            "position": position,
            "duration": segment_length
        }
