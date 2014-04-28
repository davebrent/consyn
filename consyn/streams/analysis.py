# -*- coding: utf-8 -*-
import aubio
import numpy

from .base import AnalysisSteam


__all__ = ["SampleAnalyser"]


def _slice_array(arr, bufsize=1024, hopsize=512):
    position = 0
    duration = arr.shape[0]
    while True:
        if position + bufsize >= duration:
            yield arr[position:]
            break
        else:
            yield arr[position:position + bufsize]
        position += hopsize


class SampleAnalyser(AnalysisSteam):

    def __init__(self, samplerate=44100, winsize=1024, hopsize=512, filters=40,
                 coeffs=13):
        super(SampleAnalyser, self).__init__()
        self.winsize = winsize
        self.hopsize = hopsize
        self.descriptors = {}
        self.methods = ["default", "energy", "hfc", "complex", "phase",
                        "specdiff", "kl", "mkl", "specflux", "centroid",
                        "slope", "rolloff", "spread", "skewness", "kurtosis",
                        "decrease"]

        for method in self.methods:
            self.descriptors[method] = aubio.specdesc(method, self.winsize)

        self.pvocoder = aubio.pvoc(self.winsize, self.hopsize)
        self.mfcc_feature = aubio.mfcc(winsize, filters, coeffs, samplerate)
        self.mfccs = numpy.zeros([13, ])
        self.coeffs = coeffs
        self.filters = filters

    def analyse(self, frame):
        samples = frame.samples
        features = {}
        frames = _slice_array(samples,
                              bufsize=self.winsize,
                              hopsize=self.hopsize)

        for frame in frames:
            fftgrain = self.pvocoder(frame)

            mfcc_out = self.mfcc_feature(fftgrain)
            self.mfccs = numpy.vstack((self.mfccs, mfcc_out))

            for method in self.methods:
                features[method] = self.descriptors[method](fftgrain)[0]

        for method in self.methods:
            features[method] = numpy.mean(features[method])

        mfccs = numpy.mean(self.mfccs, axis=0)
        for index, value in enumerate(list(mfccs)):
            features["mfcc_{}".format(index)] = value

        return features
