#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A concatenative synthesis command line tool.

usage: consyn [--version] [--help] <command> [<args>...]

options:
   -h, --help
   -v, --version
"""
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..models import Base
from ..settings import DATABASE_URL

from .add import command as cmd_add
from .status import command as cmd_status
from .mosaic import command as cmd_mosaic
from .remove import command as cmd_remove
from .commands import command as cmd_commands


commands = {
    "add": cmd_add,
    "status": cmd_status,
    "mosaic": cmd_mosaic,
    "remove": cmd_remove,
    "commands": cmd_commands
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print(__doc__)
    else:
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        commands[sys.argv[1]](Session())
