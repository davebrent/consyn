#!/usr/bin/env python
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

import click
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..models import Base
from ..settings import DATABASE_URL


__all__ = ["configurator", "main"]


COMMANDS = ["add", "ls", "rm", "mosaic", "show"]


class Config(object):

    def __init__(self):
        self.database = DATABASE_URL
        self.debug = False
        self.verbose = True
        self.session = None


configurator = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option("--debug", default=True, is_flag=True,
              help="Enables debug mode.")
@click.option("--verbose", default=True, is_flag=True,
              help="Enables verbose mode.")
@click.option("--database", default=DATABASE_URL,
              help="Path to database.")
@configurator
def main(config, debug, verbose, database=DATABASE_URL):
    """A concatenative synthesis command line tool."""
    engine = create_engine(database)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    config.debug = debug
    config.database = database
    config.session = Session()


for cmd in COMMANDS:
    try:
        module = __import__('consyn.cli.' + cmd.encode('ascii', 'replace'),
                            None, None, 1)
        main.add_command(getattr(module, 'command'))
    except ImportError:
        continue
