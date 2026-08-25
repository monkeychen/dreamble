from __future__ import annotations

import json
from pathlib import Path
import unittest

from equity_scenario_model import calculate_model
from grade_equity_numeric_output import grade_output


SKILL_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = SKILL_ROOT / "evals" / "fixtures" / "cross-listed-scenario.json"


class EquityNumericOutputGraderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.actual = {"calculation_result": calculate_model(self.fixture)}

    def test_accepts_matching_skill_artifact(self) -> None:
        self.assertEqual(grade_output(self.fixture, self.actual), [])

    def test_rejects_wrong_target_price(self) -> None:
        self.actual["calculation_result"]["scenarios"][1]["target_price_quote"] = 99
        errors = grade_output(self.fixture, self.actual)
        self.assertTrue(any("scenarios.base.target_price_quote" in item for item in errors))

    def test_rejects_missing_scenario(self) -> None:
        self.actual["calculation_result"]["scenarios"] = []
        errors = grade_output(self.fixture, self.actual)
        self.assertTrue(any("scenarios.base: missing" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
