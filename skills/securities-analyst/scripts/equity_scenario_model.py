#!/usr/bin/env python3
"""Calculate auditable scenario values and expected shareholder returns."""

from __future__ import annotations

import argparse
from datetime import date
import json
import math
from pathlib import Path
from typing import Any


def _number(value: Any, field: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field} must be finite")
    if positive and result <= 0:
        raise ValueError(f"{field} must be greater than zero")
    return result


def _parse_date(value: Any, field: str) -> date:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO date") from exc


def calculate_model(model: dict[str, Any]) -> dict[str, Any]:
    as_of = _parse_date(model.get("as_of"), "as_of")
    valuation_date = _parse_date(model.get("valuation_date"), "valuation_date")
    horizon_years = (valuation_date - as_of).days / 365.25
    if horizon_years <= 0:
        raise ValueError("valuation_date must be after as_of")

    spot_price_quote = _number(model.get("spot_price_quote"), "spot_price_quote", positive=True)
    security = model.get("security")
    if not isinstance(security, dict):
        raise ValueError("security must be an object")

    ordinary_per_listed = _number(
        security.get("ordinary_shares_per_listed_unit"),
        "security.ordinary_shares_per_listed_unit",
        positive=True,
    )
    quote_units_per_currency = _number(
        security.get("quote_units_per_listing_currency", 1),
        "security.quote_units_per_listing_currency",
        positive=True,
    )

    scenarios = model.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("scenarios must be a non-empty array")

    probability_total = 0.0
    weighted_terminal_wealth = 0.0
    output_scenarios: list[dict[str, Any]] = []

    for index, scenario in enumerate(scenarios):
        if not isinstance(scenario, dict):
            raise ValueError(f"scenarios[{index}] must be an object")
        prefix = f"scenarios[{index}]"
        name = scenario.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError(f"{prefix}.name must be a non-empty string")

        probability = _number(scenario.get("probability"), f"{prefix}.probability")
        if probability < 0 or probability > 1:
            raise ValueError(f"{prefix}.probability must be between zero and one")
        probability_total += probability

        has_enterprise_value = "enterprise_value" in scenario
        has_equity_value = "equity_value" in scenario
        if has_enterprise_value == has_equity_value:
            raise ValueError(f"{prefix} must contain exactly one of enterprise_value or equity_value")

        if has_enterprise_value:
            enterprise_value = _number(scenario["enterprise_value"], f"{prefix}.enterprise_value")
            net_debt = _number(scenario.get("net_debt", 0), f"{prefix}.net_debt")
            minority_interest = _number(
                scenario.get("minority_interest", 0), f"{prefix}.minority_interest"
            )
            non_operating_assets = _number(
                scenario.get("non_operating_assets", 0), f"{prefix}.non_operating_assets"
            )
            equity_value = enterprise_value - net_debt - minority_interest + non_operating_assets
            bridge = {
                "enterprise_value": enterprise_value,
                "net_debt": net_debt,
                "minority_interest": minority_interest,
                "non_operating_assets": non_operating_assets,
            }
        else:
            equity_value = _number(scenario["equity_value"], f"{prefix}.equity_value")
            bridge = {"equity_value_input": equity_value}

        diluted_shares = _number(
            scenario.get("diluted_ordinary_shares"),
            f"{prefix}.diluted_ordinary_shares",
            positive=True,
        )
        dividends_quote = _number(
            scenario.get("cumulative_dividends_quote", 0),
            f"{prefix}.cumulative_dividends_quote",
        )
        if dividends_quote < 0:
            raise ValueError(f"{prefix}.cumulative_dividends_quote cannot be negative")
        target_fx = _number(
            scenario.get("target_listing_currency_per_valuation_currency"),
            f"{prefix}.target_listing_currency_per_valuation_currency",
            positive=True,
        )

        raw_equity_value = equity_value
        equity_value = max(0.0, raw_equity_value)

        value_per_ordinary_valuation = equity_value / diluted_shares
        target_price_listing = (
            value_per_ordinary_valuation * ordinary_per_listed * target_fx
        )
        target_price_quote = target_price_listing * quote_units_per_currency
        terminal_wealth_quote = target_price_quote + dividends_quote
        total_return = terminal_wealth_quote / spot_price_quote - 1
        annualized_return = (terminal_wealth_quote / spot_price_quote) ** (1 / horizon_years) - 1
        weighted_terminal_wealth += probability * terminal_wealth_quote

        output_scenarios.append(
            {
                "name": name,
                "probability": probability,
                "raw_equity_value": raw_equity_value,
                "equity_value": equity_value,
                "equity_floor_applied": raw_equity_value < 0,
                "value_per_ordinary_share_valuation_currency": value_per_ordinary_valuation,
                "target_listing_currency_per_valuation_currency": target_fx,
                "target_price_listing_currency": target_price_listing,
                "target_price_quote": target_price_quote,
                "cumulative_dividends_quote": dividends_quote,
                "terminal_wealth_quote": terminal_wealth_quote,
                "total_return": total_return,
                "annualized_return": annualized_return,
                "bridge": bridge,
            }
        )

    if not math.isclose(probability_total, 1.0, rel_tol=0, abs_tol=1e-9):
        raise ValueError(f"scenario probabilities must sum to 1, got {probability_total}")

    expected_total_return = weighted_terminal_wealth / spot_price_quote - 1
    expected_annualized_return = (
        weighted_terminal_wealth / spot_price_quote
    ) ** (1 / horizon_years) - 1

    return {
        "as_of": as_of.isoformat(),
        "valuation_date": valuation_date.isoformat(),
        "horizon_years": horizon_years,
        "valuation_currency": model.get("valuation_currency"),
        "security": security,
        "spot_price_quote": spot_price_quote,
        "scenarios": output_scenarios,
        "probability_weighted_terminal_wealth_quote": weighted_terminal_wealth,
        "probability_weighted_total_return": expected_total_return,
        "probability_weighted_annualized_return": expected_annualized_return,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Path to an equity scenario JSON file")
    args = parser.parse_args()
    model = json.loads(args.input.read_text(encoding="utf-8"))
    result = calculate_model(model)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
