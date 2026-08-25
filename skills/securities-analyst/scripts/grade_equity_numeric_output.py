#!/usr/bin/env python3
"""Compare a Skill numeric artifact with a deterministic scenario model."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from equity_scenario_model import calculate_model


TOP_LEVEL_FIELDS = (
    "probability_weighted_terminal_wealth_quote",
    "probability_weighted_total_return",
    "probability_weighted_annualized_return",
)
SCENARIO_FIELDS = (
    "raw_equity_value",
    "equity_value",
    "target_listing_currency_per_valuation_currency",
    "target_price_quote",
    "terminal_wealth_quote",
    "total_return",
    "annualized_return",
)


def _actual_payload(actual: dict[str, Any]) -> dict[str, Any]:
    payload = actual.get("calculation_result", actual)
    if not isinstance(payload, dict):
        raise ValueError("actual output must be an object or contain calculation_result")
    return payload


def _compare_number(
    errors: list[str], field: str, expected: Any, actual: Any, tolerance: float
) -> None:
    if isinstance(actual, bool) or not isinstance(actual, (int, float)):
        errors.append(f"{field}: missing or non-numeric")
        return
    if not math.isclose(float(actual), float(expected), rel_tol=tolerance, abs_tol=tolerance):
        errors.append(f"{field}: expected {expected}, got {actual}")


def grade_output(
    fixture: dict[str, Any], actual: dict[str, Any], tolerance: float = 1e-4
) -> list[str]:
    expected = calculate_model(fixture)
    payload = _actual_payload(actual)
    errors: list[str] = []

    for field in TOP_LEVEL_FIELDS:
        _compare_number(errors, field, expected[field], payload.get(field), tolerance)

    actual_scenarios = payload.get("scenarios")
    if not isinstance(actual_scenarios, list):
        return errors + ["scenarios: missing or not an array"]
    actual_by_name = {
        item.get("name"): item for item in actual_scenarios if isinstance(item, dict)
    }
    for expected_scenario in expected["scenarios"]:
        name = expected_scenario["name"]
        actual_scenario = actual_by_name.get(name)
        if actual_scenario is None:
            errors.append(f"scenarios.{name}: missing")
            continue
        for field in SCENARIO_FIELDS:
            _compare_number(
                errors,
                f"scenarios.{name}.{field}",
                expected_scenario[field],
                actual_scenario.get(field),
                tolerance,
            )
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    parser.add_argument("actual", type=Path)
    parser.add_argument("--tolerance", type=float, default=1e-4)
    args = parser.parse_args()

    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    actual = json.loads(args.actual.read_text(encoding="utf-8"))
    errors = grade_output(fixture, actual, args.tolerance)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print("equity numeric output: OK")


if __name__ == "__main__":
    main()
