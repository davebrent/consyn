#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A concatenative synthesis command line tool.

usage: consyn [--version] [--help] <command> [<args>...]

options:
   -h, --help
   -v, --version

commands:
    add, show, remove, mosaic, status

"""
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..models import Base
from ..settings import DATABASE_URL

from .add import command as cmd_add
from .mosaic import command as cmd_mosaic
from .remove import command as cmd_remove
from .show import command as cmd_show
from .status import command as cmd_status


commands = {
    "add": cmd_add,
    "show": cmd_show,
    "status": cmd_status,
    "mosaic": cmd_mosaic,
    "remove": cmd_remove
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print(__doc__)
    else:
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        commands[sys.argv[1]](Session())
