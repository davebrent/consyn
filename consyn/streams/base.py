# -*- coding: utf-8 -*-
import inspect
import collections


__all__ = [
    "AudioFrame",
    "Stream",
    "StreamFactory",
    "FrameLoaderStream",
    "UnitLoaderStream",
    "SliceStream",
    "SelectionStream",
    "ResynthesisStream",
    "AnalysisSteam"
]


class AudioFrame(object):
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
        values = ["{}={}".format(key, getattr(self, key)) for key in keys]
        return "<AudioFrame({})>".format(", ".join(values))


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


class StreamFactory(object):

    def __new__(cls, name, **kwargs):
        if name not in cls.objects:
            raise Exception
        Class = cls.objects[name]
        args, _, _, defaults = inspect.getargspec(Class.__init__)
        args = args[-len(defaults):]
        kwargs = {key: kwargs[key] for key in args if key in kwargs}
        return Class(**kwargs)


class FrameLoaderStream(Stream):

    def __init__(self, bufsize=1024, hopsize=512,
                 key=lambda pool: pool["path"]):
        super(FrameLoaderStream, self).__init__()
        self.bufsize = bufsize
        self.hopsize = hopsize
        self.key = key

    def __call__(self, pipe):
        for pool in pipe:
            path = self.key(pool)
            frames = self.read(path)
            for frame in frames:
                pool["frame"] = frame
                yield pool


class UnitLoaderStream(Stream):

    def __init__(self, bufsize=1024, hopsize=512,
                 key=lambda pool: pool["path"]):
        super(UnitLoaderStream, self).__init__()
        self.bufsize = bufsize
        self.hopsize = hopsize
        self.key = key

    def __call__(self, pipe):
        for pool in pipe:
            path = self.key(pool)
            unit = pool["unit"]
            frames = self.read(path, unit)
            for frame in frames:
                pool["frame"] = frame
                yield pool


class SliceStream(Stream):

    def __init__(self):
        super(SliceStream, self).__init__()

    def __call__(self, pipe):
        for pool in pipe:
            _slice = self.observe(pool["frame"])
            if _slice is None:
                continue
            yield {"frame": _slice}

        closing = self.finish()
        if isinstance(closing, collections.Iterable):
            for _slice in closing:
                yield {"frame": _slice}

    def observe(self, samples, read, position, channel, samplerate, path):
        raise NotImplementedError("SliceStreams must implement this")

    def finish(self, samples, path, channel, samplerate):
        pass


class SelectionStream(Stream):

    def __init__(self, session, mediafiles):
        super(SelectionStream, self).__init__()
        self.mediafiles = [mediafile.id for mediafile in mediafiles]
        self.session = session

    def __call__(self, pipe):
        for pool in pipe:
            unit = self.select(pool["unit"])
            pool["target"] = pool["unit"]
            pool["unit"] = unit
            yield pool

    def select(self, unit):
        raise NotImplementedError("SelectionStreams must implement this")


class ResynthesisStream(Stream):

    def __init__(self):
        super(ResynthesisStream, self).__init__()

    def __call__(self, pipe):
        for pool in pipe:
            samples, unit = self.process(
                pool["frame"].samples,
                pool["unit"],
                pool["target"])

            frame = AudioFrame()
            frame.samples = samples
            pool["unit"] = unit
            pool["frame"] = frame
            yield pool

    def process(self, samples, unit, target):
        raise NotImplementedError("ResynthesisStreams must implement this")


class AnalysisSteam(Stream):

    def __init__(self):
        super(AnalysisSteam, self).__init__()

    def __call__(self, pipe):
        for pool in pipe:
            pool["features"] = self.analyse(pool["frame"])
            yield pool

    def analyse(self, samples):
        raise NotImplementedError("AnalysisSteams must return features")
