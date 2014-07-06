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
from __future__ import unicode_literals
import collections


__all__ = [
    "AudioFrame",
    "Stage",
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
        keys = ["position", "duration", "channel", "samplerate"]
        values = ["{}={}".format(key, getattr(self, key)) for key in keys
                  if hasattr(self, key)]
        return "<AudioFrame({})>".format(", ".join(values))


class Stage(object):
    pass


class Pipeline(object):

    def __init__(self, stages):
        self.stages = stages

    def run(self, *args):
        pool = self.stages[0](args)
        for stage in self.stages[1:]:
            pool = stage(pool)
        return pool


class FileLoaderStage(Stage):
    """Base class for generating a stream of AudioFrames from a file path.

    Kwargs:
      hopsize (int): The size of frames to read
      key (function): Function for getting a filepath from the current context

    """
    def __init__(self, filepath, hopsize=1024):
        self.filepath = filepath
        self.hopsize = hopsize

    def __call__(self, *args):
        for frame in self.read(self.filepath):
            yield {"frame": frame}

        if hasattr(self, "close"):
            self.close()

    def read(self, path):
        raise NotImplementedError("FileLoaderStages must implement this")


class UnitLoaderStage(Stage):
    """Base class for generating a stream of AudioFrames from Units"""
    def __init__(self, hopsize=1024, key=lambda context: context["path"]):
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

        if hasattr(self, "close"):
            self.close()

    def read(self, path, unit):
        raise NotImplementedError("UnitLoaderStages must implement this")


class SegmentationStage(Stage):
    """Base class for slicing a stream of AudioFrames"""

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

    def __call__(self, pipe):
        for context in pipe:
            samples, unit = self.process(
                context["frame"].samples,
                context["unit"],
                context["target"])
            if samples.shape[0] != 0:
                frame = AudioFrame()
                frame.samples = samples
                context["unit"] = unit
                context["frame"] = frame
                yield context

    def process(self, samples, unit, target):
        raise NotImplementedError("SynthesisStages must implement this")


class AnalysisStage(Stage):
    """Base class for analysing an AudioFrame"""

    def __call__(self, pipe):
        for context in pipe:
            features = self.analyse(context["frame"])
            if features is not None:
                context["features"] = features
                yield context

    def analyse(self, samples):
        raise NotImplementedError("AnalysisStages must return features")

    def __len__(self):
        raise NotImplementedError("AnalysisStages must implement this")
