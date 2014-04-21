import unittest
from consyn import models
from consyn import settings


class FeaturesTests(unittest.TestCase):

    def test_init_features(self):
        features = models.Features(False, {
            "feat_1": 0.1,
            "feat_2": 0.2,
            "feat_3": 0.3
        })

        self.assertEqual(features["feat_1"], 0.1)
        self.assertEqual(features["feat_2"], 0.2)
        self.assertEqual(features["feat_3"], 0.3)

    def test_to_many_features(self):
        feats = {}
        for index in range(settings.FEATURE_SLOTS + 1):
            feats["test_{}".format(index)] = index
        self.assertRaises(AssertionError, models.Features, False, feats)
