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
"""Base classes for processing media files"""
import collections
import inspect


__all__ = [
    "AudioFrame",
    "Stage",
    "StageFactory",
    "FileLoaderStage",
    "UnitLoaderStage",
    "SegmentationStage",
    "SelectionStage",
    "SynthesisStage",
    "AnalysisStage"
]


class AudioFrame(object):
    """Container for a section of audio being processed.

    Attributes:
      samples (ndarray): Numpy array containing a section of audio samples
      samplerate (int): Sampling rate of the media file
      position (int): Position of samples in the original media file
      channel (int): The channel the samples belong to
      path (str): Path of the media file
      duration (int): Duration of the section of samples

    """
    __slots__ = [
        "samples",
        "samplerate",
        "position",
        "channel",
        "index",
        "path",
        "duration"
    ]

    def __init__(self, *args, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def __len__(self):
        return self.duration

    def __repr__(self):
        keys = ['position', 'duration', 'channel', 'samplerate']
        values = ["{}={}".format(key, getattr(self, key)) for key in keys
                  if hasattr(self, key)]
        return "<AudioFrame({})>".format(", ".join(values))


class Stage(object):

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
        return Stage.pipe(self, outpipe)

    def __rrshift__(self, inpipe):
        return Stage.pipe(inpipe, self)


class FileLoaderStage(Stage):
    """Base class for generating a stream of AudioFrames from a file path.

    Kwargs:
      hopsize (int): The size of frames to read
      key (function): Function for getting a filepath from the current context

    """
    def __init__(self, hopsize=1024, key=lambda context: context["path"]):
        super(FileLoaderStage, self).__init__()
        self.hopsize = hopsize
        self.key = key

    def __call__(self, pipe):
        for context in pipe:
            path = self.key(context)
            frames = self.read(path)
            for frame in frames:
                context["frame"] = frame
                yield context

    def read(self, path):
        raise NotImplementedError("FileLoaderStages must implement this")


class UnitLoaderStage(Stage):
    """Base class for generating a stream of AudioFrames from Units"""
    def __init__(self, hopsize=1024, key=lambda context: context["path"]):
        super(UnitLoaderStage, self).__init__()
        self.hopsize = hopsize
        self.key = key

    def __call__(self, pipe):
        for context in pipe:
            path = self.key(context)
            unit = context["unit"]
            frames = self.read(path, unit)
            for frame in frames:
                context["frame"] = frame
                yield context

    def read(self, path, unit):
        raise NotImplementedError("UnitLoaderStages must implement this")


class SegmentationStage(Stage):
    """Base class for slicing a stream of AudioFrames"""
    def __init__(self):
        super(SegmentationStage, self).__init__()

    def __call__(self, pipe):
        for context in pipe:
            _slice = self.observe(context["frame"])
            if _slice is None:
                continue
            yield {"frame": _slice}

        closing = self.finish()
        if isinstance(closing, collections.Iterable):
            for _slice in closing:
                yield {"frame": _slice}

    def observe(self, frame):
        raise NotImplementedError("SegmentationStages must implement this")

    def finish(self):
        pass


class SelectionStage(Stage):
    """Base class for unit selection algorithms"""
    def __init__(self, session, mediafiles):
        super(SelectionStage, self).__init__()
        self.mediafiles = [mediafile.id for mediafile in mediafiles]
        self.session = session

    def __call__(self, pipe):
        for context in pipe:
            unit = self.select(context["unit"])
            context["target"] = context["unit"]
            context["unit"] = unit
            yield context

    def select(self, unit):
        raise NotImplementedError("SelectionStages must implement this")


class SynthesisStage(Stage):
    """Base class for processing units before concatenation"""
    def __init__(self):
        super(SynthesisStage, self).__init__()

    def __call__(self, pipe):
        for context in pipe:
            samples, unit = self.process(
                context["frame"].samples,
                context["unit"],
                context["target"])

            frame = AudioFrame()
            frame.samples = samples
            context["unit"] = unit
            context["frame"] = frame
            yield context

    def process(self, samples, unit, target):
        raise NotImplementedError("SynthesisStages must implement this")


class AnalysisStage(Stage):
    """Base class for analysing an AudioFrame"""
    def __init__(self):
        super(AnalysisStage, self).__init__()

    def __call__(self, pipe):
        for context in pipe:
            context["features"] = self.analyse(context["frame"])
            yield context

    def analyse(self, samples):
        raise NotImplementedError("AnalysisStages must return features")


class StageFactory(object):

    def __new__(cls, name, **kwargs):
        if name not in cls.objects:
            raise Exception
        Class = cls.objects[name]
        args, _, _, defaults = inspect.getargspec(Class.__init__)
        args = args[-len(defaults):]
        kwargs = {key: kwargs[key] for key in args if key in kwargs}
        return Class(**kwargs)
