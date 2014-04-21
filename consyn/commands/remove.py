# -*- coding: utf-8 -*-
"""Remove corpi

usage: consyn remove <corpi>...

"""
import docopt
from clint.textui import colored
from clint.textui import puts

from .. import models


def command(session, paths=None, verbose=True, force=False):
    args = docopt.docopt(__doc__)
    ids = args["<corpi>"]

    if len(ids) == 1 and ids[0] == "all":
        ids = [corpus.id for corpus in session.query(models.Corpus).all()]

    for pk in ids:
        corpus = session.query(models.Corpus).get(int(pk))

        if not corpus:
            puts(colored.red("Corpus {} not found".format(pk)))
            continue

        for feature in corpus.features:
            session.delete(feature)

        for unit in corpus.units:
            session.delete(unit)

        session.delete(corpus)
        session.commit()
