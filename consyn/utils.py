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
import inspect

from .base import Stage


__all__ = [
    "UnitGenerator",
    "slice_array"
]


class UnitGenerator(Stage):

    def __init__(self, mediafile, session):
        super(UnitGenerator, self).__init__()
        self.mediafile = mediafile
        self.session = session

    def __call__(self, *args):
        for unit in self.mediafile.units:
            yield {"unit": unit}


def slice_array(arr, bufsize=1024, hopsize=512):
    position = 0
    duration = arr.shape[0]
    while True:
        if position >= duration:
            raise StopIteration
        if position + bufsize >= duration:
            yield arr[position:]
            raise StopIteration
        else:
            yield arr[position:position + bufsize]
        position += hopsize


def factory(objects, name, *args, **kwargs):
    if name not in objects:
        raise Exception("{} not found".format(name))

    Class = objects[name]
    kargs, _, _, defaults = inspect.getargspec(Class.__init__)

    if defaults is not None:
        kargs = kargs[-len(defaults):]

    kwargs = {key: kwargs[key] for key in kargs if key in kwargs}
    return Class(*args, **kwargs)
