import unittest

import pandas as pd

from analysis.comprehension.models import fit_reverse


class ModelTests(unittest.TestCase):
    def test_reverse_model_accepts_two_question_scores(self):
        data = pd.DataFrame(
            {
                "participant_id": ["p1", "p1", "p2", "p2"],
                "wave": [1, 1, 1, 1],
                "lang": ["en", "en", "en", "en"],
                "text_id": [1, 2, 1, 2],
                "fixations_per_word": [1.0, 1.2, 1.1, 1.3],
                "comprehension_score": [2, 1, 1, 0],
            }
        )
        result = fit_reverse(data)
        self.assertTrue(result.converged)
        self.assertIn("fixations_per_word", result.params.index)


if __name__ == "__main__":
    unittest.main()
