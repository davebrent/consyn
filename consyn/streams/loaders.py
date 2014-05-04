import logging

import aubio
import numpy

from .base import AudioFrame
from .base import FrameLoaderStream
from .base import UnitLoaderStream
from ..settings import DTYPE


__all__ = [
    "AubioFrameLoader",
    "AubioUnitLoader"
]


logger = logging.getLogger(__name__)


class AubioFrameLoader(FrameLoaderStream):

    def read(self, path):
        soundfile = aubio.source(path, 0, self.bufsize)
        soundfile.seek(0)

        index = 0
        positions = {}

        while True:
            channels, read = soundfile.do_multi()

            for channel, samples in enumerate(channels):
                if channel not in positions:
                    positions[channel] = 0

                frame = AudioFrame()
                frame.samplerate = soundfile.samplerate
                frame.position = positions[channel]
                frame.channel = channel
                frame.samples = samples
                frame.duration = read
                frame.index = index
                frame.path = path

                positions[channel] += read
                yield frame

            index += 1
            if read < soundfile.hop_size:
                break

        soundfile.close()
        del soundfile
        logger.debug("Closing soundfile for {}".format(path))


class AubioUnitLoader(UnitLoaderStream):

    def read(self, path, unit):
        soundfile = aubio.source(path, 0, self.bufsize)
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

        soundfile.close()
        del soundfile
        logger.debug("Closing soundfile for {}".format(path))
        yield frame
