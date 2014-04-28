import aubio
import numpy

from .base import Pool
from .base import Stream
from ..models import Corpus
from ..settings import DTYPE


__all__ = [
    "UnitGenerator",
    "CorpusSampleBuilder",
    "CorpusWriter"
]


class UnitGenerator(Stream):

    def __init__(self, session):
        super(UnitGenerator, self).__init__()
        self.session = session

    def __call__(self, pipe):
        for pool in pipe:
            if not isinstance(pool["corpus"], Corpus):
                pool["corpus"] = Corpus.by_id_or_name(
                    self.session, pool["corpus"])

            for unit in pool["corpus"].units:
                pool["unit"] = unit
                yield pool


class CorpusSampleBuilder(Stream):

    def __init__(self, unit_key="unit", channels=2):
        super(CorpusSampleBuilder, self).__init__()
        self.unit_key = unit_key
        self.channels = channels
        self.buffers = {}
        self.counts = {}
        self.end = {}

    def __call__(self, pipe):
        for pool in pipe:
            corpus = pool["corpus"]
            target = pool[self.unit_key]
            samples = pool["frame"].samples

            if corpus.path in self.end:
                continue

            if corpus.path not in self.buffers:
                self.counts[corpus.path] = 0
                self.buffers[corpus.path] = numpy.zeros(
                    (corpus.channels, corpus.duration),
                    dtype=DTYPE)

            buff = self.buffers[corpus.path]

            buff[target.channel][
                target.position:target.position + target.duration] = samples
            self.counts[corpus.path] += 1

            if self.counts[corpus.path] == len(corpus.units) and \
                    corpus.path not in self.end:
                self.end[corpus.path] = True

                new_pool = Pool(initial={
                    "corpus": pool["corpus"],
                    "buffer": buff
                })

                if pool.values.get("out"):
                    new_pool["out"] = pool["out"]

                yield new_pool


class CorpusWriter(Stream):

    def __call__(self, pipe):
        for pool in pipe:
            framesize = 1024
            corpus = pool["corpus"]
            buff = pool["buffer"]
            outfile = pool["out"]

            sink = aubio.sink(outfile, 0, corpus.channels)
            out_samples = numpy.array_split(buff, framesize, axis=1)

            for frame in out_samples:
                amount = frame[0].shape[0]
                sink.do_multi(frame, amount)

            sink.close()
            del sink

            yield Pool(initial={"out": pool["out"]})
