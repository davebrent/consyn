# -*- coding: utf-8 -*-
"""Print all available commands

usage: consyn commands

"""
from docopt import docopt


def command(session, paths=None, verbose=True, force=False):
    docopt(__doc__)
    from . import commands
    for command in commands.keys():
        print command
