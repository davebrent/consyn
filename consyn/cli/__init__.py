#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A concatenative synthesis command line tool.

usage: consyn [options] <command> [<args>...]

options:
   -h, --help
   -v, --version
   -d, --database

commands:
    add, show, remove, mosaic, ls

"""
from docopt import docopt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..models import Base
from ..settings import DATABASE_URL
from .add import command as cmd_add
from .mosaic import command as cmd_mosaic
from .remove import command as cmd_remove
from .show import command as cmd_show
from .ls import command as cmd_ls


commands = {
    "add": cmd_add,
    "show": cmd_show,
    "ls": cmd_ls,
    "mosaic": cmd_mosaic,
    "remove": cmd_remove
}


def main():
    args = docopt(__doc__, help=False)
    if args["<command>"] not in commands:
        print(__doc__)
    else:
        db_url = DATABASE_URL
        if args["--database"]:
            db_url = args["--database"]

        engine = create_engine(db_url)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        commands[args["<command>"]](Session())
