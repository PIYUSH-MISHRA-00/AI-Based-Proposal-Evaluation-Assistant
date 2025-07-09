import unittest
from evaluator import (
    load_weights,
    extract_sections,
    score_cost_section,
    heuristic_score_section,
    score_sections_with_optional_gemini,
)

class TestEvaluator(unittest.TestCase):

    def test_load_weights(self):
        weights = load_weights()
        self.assertIn("cost", weights)
        self.assertIn("technical_merit", weights)
        self.assertIn("past_performance", weights)

    def test_extract_sections(self):
        text = """
        Cost: $1000
        Technical Approach: We have experience and quality.
        Past Performance: Reliable and efficient.
        """
        sections = extract_sections(text)
        self.assertIn("cost", sections)
        self.assertIn("technical_merit", sections)
        self.assertIn("past_performance", sections)
        self.assertTrue("1000" in sections["cost"])
        self.assertTrue("experience" in sections["technical_merit"])
        self.assertTrue("Reliable" in sections["past_performance"])

    def test_score_cost_section(self):
        cost_text = "Cost: $1000"
        score = score_cost_section(cost_text, all_costs=[1000, 2000, 3000])
        self.assertTrue(0 <= score <= 100)

    def test_heuristic_score_section(self):
        text = "We have experience and quality."
        score = heuristic_score_section(text)
        self.assertTrue(0 <= score <= 100)

    def test_score_sections_with_optional_gemini_heuristic(self):
        sections = {
            "cost": "Cost: $1000",
            "technical_merit": "We have experience and quality.",
            "past_performance": "Reliable and efficient."
        }
        weights = {"cost": 0.3, "technical_merit": 0.4, "past_performance": 0.3}
        # Remove all_costs argument as it is not accepted by the function
        scores = score_sections_with_optional_gemini(sections, weights, api_key=None)
        self.assertIn("final_score", scores)
        self.assertTrue(0 <= scores["final_score"] <= 100)

if __name__ == "__main__":
    unittest.main()
