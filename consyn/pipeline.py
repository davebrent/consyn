# -*- coding: utf-8 -*-


class Task(object):

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
        return Task.pipe(self, outpipe)

    def __rrshift__(self, inpipe):
        return Task.pipe(inpipe, self)


class State(object):

    def __init__(self, initial={}):
        self.values = initial

    def __getattr__(self, name):
        return self.values[name]

    def __getitem__(self, name):
        return self.values[name]

    def __setitem__(self, name, value):
        self.values[name] = value

    def values(self):
        return self.values

    def __delitem__(self, name):
        del self.values[name]

    def __str__(self):
        return self.values.__str__()
