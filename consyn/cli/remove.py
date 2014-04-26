# -*- coding: utf-8 -*-
"""Remove corpi

usage: consyn remove <corpi>...

"""
import docopt
from clint.textui import colored
from clint.textui import puts

from .. import models
from .. import commands


def command(session, paths=None, verbose=True, force=False):
    args = docopt.docopt(__doc__)
    corpi = args["<corpi>"]

    if len(corpi) == 1 and corpi[0] == "all":
        corpi = [corpus.id for corpus in session.query(models.Corpus).all()]

    for param in corpi:
        corpus = models.Corpus.by_id_or_name(session, param)
        if not corpus:
            puts(colored.red("Corpus {} not found".format(param)))
            continue

        commands.remove_corpus(session, corpus)
