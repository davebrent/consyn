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
from ConfigParser import RawConfigParser
import os
from StringIO import StringIO

import click
from sqlalchemy import Float


APP_NAME = "Consyn"
APP_DIR = click.get_app_dir(APP_NAME)

FEATURE_SLOTS = 29
FEATURE_TYPE = Float
DTYPE = "float32"

CONFIG_PATH = os.path.join(APP_DIR, "config.ini")
DEFAULT_CONFIG = """
[consyn]
bufsize = 1024
hopsize = 512
database = {0}
max_open_files = 50

[consyn.commands:add_mediafile]
segmentation = onsets
bufsize = 1024
hopsize = 512
segmentation = onsets
method = default
threshold = 0.3
silence = -90

""".format(os.path.join(APP_DIR, "consyn.sqlite"))

if not os.path.isdir(APP_DIR):
    os.makedirs(APP_DIR)

if not os.path.isfile(CONFIG_PATH):
    with open(CONFIG_PATH, "w") as conf:
        conf.write(DEFAULT_CONFIG)


user = RawConfigParser()
user.read(CONFIG_PATH)

_defaults = StringIO()
_defaults.write(DEFAULT_CONFIG)
_defaults.seek(0)

defaults = RawConfigParser()
defaults.readfp(_defaults)
_defaults.close()


def _maybe_number(value):
    fn = float if "." in value else int
    try:
        value = fn(value)
    except ValueError:
        pass
    return value


def _get_section(section):
    conf = {}
    if not defaults.has_section(section):
        return conf
    for name, value in defaults.items(section):
        try:
            value = user.get(section, name)
        except:
            pass
        conf[name] = _maybe_number(value)
    return conf


def get_settings(module, name=None):
    conf = {}
    if name is not None:
        module = module + ":" + name
    conf.update(_get_section("consyn"))
    conf.update(_get_section(module))
    return conf
