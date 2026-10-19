import unittest

import pandas as pd

from analysis.comprehension.io import load_counts, sample_summary


class LoadCountsTests(unittest.TestCase):
    def test_both_waves_load_and_have_unique_keys(self):
        data = load_counts("both")
        self.assertEqual(len(data), 14196)
        self.assertFalse(data.duplicated(["participant_id", "wave", "text_id"]).any())
        self.assertTrue(data["comprehension_score"].between(0, 2).all())
        self.assertTrue((data["text_length_words"] > 0).all())

    def test_sample_summary_has_wave_rows(self):
        data = load_counts("1")
        summary = sample_summary(data)
        self.assertEqual(summary["wave"].unique().tolist(), [1])
        self.assertIsInstance(summary, pd.DataFrame)


if __name__ == "__main__":
    unittest.main()
