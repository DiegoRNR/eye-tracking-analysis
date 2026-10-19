import unittest

from analysis.integrated.io import load_integrated


class IntegratedLoadTests(unittest.TestCase):
    def test_join_preserves_participant_text_rows(self):
        data = load_integrated("both")
        self.assertEqual(len(data), 14196)
        self.assertFalse(data.duplicated(["participant_id", "wave", "text_id"]).any())
        self.assertGreater(data["language_skill_composite"].notna().sum(), 0)


if __name__ == "__main__":
    unittest.main()
