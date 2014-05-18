#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A concatenative synthesis command line tool.

usage: consyn [options] <command> [<args>...]

options:
   -h, --help
   -v, --version
   -d, --database

commands:
    add, show, rm, mosaic, ls
"""
import sys

from docopt import docopt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..models import Base
from ..settings import DATABASE_URL
from .add import command as cmd_add
from .mosaic import command as cmd_mosaic
from .rm import command as cmd_rm
from .show import command as cmd_show
from .ls import command as cmd_ls


commands = {
    "add": cmd_add,
    "ls": cmd_ls,
    "mosaic": cmd_mosaic,
    "rm": cmd_rm,
    "show": cmd_show
}


def main():
    args = docopt(__doc__, help=False)
    params = sys.argv[1:]

    if args["<command>"] not in commands:
        print(__doc__)
    else:
        db_url = DATABASE_URL
        if args["--database"]:
            db_url = args["--database"]
            params.pop(0)

        engine = create_engine(db_url)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        commands[args["<command>"]](Session(), argv=params)
