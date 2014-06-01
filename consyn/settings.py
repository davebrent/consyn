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
import logging
import os
import logging.config

from sqlalchemy import Float


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
BUFSIZE = 1024
HOPSIZE = 512
FEATURE_SLOTS = 29
FEATURE_TYPE = Float
DATABASE_PATH = os.path.join(ROOT_DIR, "consyn.sqlite")
DATABASE_URL = "sqlite:///{}".format(DATABASE_PATH)
DTYPE = "float32"
OPEN_FILE_MAX = 50

logging.config.fileConfig(os.path.join(ROOT_DIR, "development.ini"))
