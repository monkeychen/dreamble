from __future__ import annotations

import json
from pathlib import Path
import unittest

from equity_scenario_model import calculate_model


SKILL_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = SKILL_ROOT / "evals" / "fixtures" / "cross-listed-scenario.json"


class EquityScenarioModelTest(unittest.TestCase):
    def setUp(self) -> None:
        self.model = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_cross_listed_bridge_and_expected_return(self) -> None:
        result = calculate_model(self.model)
        scenarios = {item["name"]: item for item in result["scenarios"]}

        self.assertAlmostEqual(scenarios["base"]["equity_value"], 900.0)
        self.assertAlmostEqual(scenarios["base"]["target_price_quote"], 10.08)
        self.assertAlmostEqual(result["probability_weighted_terminal_wealth_quote"], 10.5)
        self.assertAlmostEqual(result["probability_weighted_total_return"], 0.3125)
        self.assertAlmostEqual(result["probability_weighted_annualized_return"], 0.14554, places=4)

    def test_probabilities_must_sum_to_one(self) -> None:
        self.model["scenarios"][0]["probability"] = 0.2
        with self.assertRaisesRegex(ValueError, "probabilities must sum to 1"):
            calculate_model(self.model)

    def test_scenario_requires_one_valuation_basis(self) -> None:
        self.model["scenarios"][0]["equity_value"] = 600
        with self.assertRaisesRegex(ValueError, "exactly one"):
            calculate_model(self.model)

    def test_failure_scenario_allows_zero_equity_value(self) -> None:
        scenario = self.model["scenarios"][0]
        scenario["enterprise_value"] = 50
        scenario["cumulative_dividends_quote"] = 0
        result = calculate_model(self.model)
        bear = result["scenarios"][0]
        self.assertLess(bear["raw_equity_value"], 0)
        self.assertEqual(bear["equity_value"], 0)
        self.assertTrue(bear["equity_floor_applied"])
        self.assertEqual(bear["total_return"], -1)


if __name__ == "__main__":
    unittest.main()
