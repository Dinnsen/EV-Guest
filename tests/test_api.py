"""Unit tests for EV Guest API helpers."""

from __future__ import annotations

from custom_components.ev_guest import api


def test_clean_identifier_removes_spaces_and_symbols() -> None:
    assert api.clean_identifier("EN 17-765") == "EN17765"
    assert api.clean_identifier(" wb-123_aa ") == "WB123AA"


def test_normalize_text_keeps_letters_numbers_and_plus() -> None:
    assert api.normalize_text("EQB 250+") == "eqb250+"
    assert api.normalize_text("Mercedes-Benz") == "mercedesbenz"
    assert api.normalize_text(None) == ""


def test_extract_float_handles_multiple_input_types() -> None:
    assert api._extract_float(77) == 77.0
    assert api._extract_float("77,4 kWh") == 77.4
    assert api._extract_float("usable 66.5") == 66.5
    assert api._extract_float(None) is None
    assert api._extract_float("not a number") is None


def test_extract_candidates_supports_nested_open_ev_data_shapes() -> None:
    payload = {
        "brand": "Mercedes-Benz",
        "vehicles": [
            {
                "model": "EQB",
                "variant": "250+",
                "battery": {"usable_kwh": "66.5"},
                "model_year": 2024,
            },
            {
                "model": "EQB",
                "variant": "300 4MATIC",
                "battery_capacity": 70.5,
                "release_year": 2023,
            },
        ],
    }

    candidates = api._extract_candidates(payload)

    assert {
        "brand": "Mercedes-Benz",
        "model": "EQB",
        "variant": "250+",
        "model_year": 2024,
        "battery_capacity": 66.5,
    } in candidates
    assert {
        "brand": "Mercedes-Benz",
        "model": "EQB",
        "variant": "300 4MATIC",
        "model_year": 2023,
        "battery_capacity": 70.5,
    } in candidates


def test_score_candidate_prefers_exact_variant_and_year_match() -> None:
    exact = {
        "brand": "Mercedes",
        "model": "EQB",
        "variant": "250+",
        "model_year": 2024,
    }
    near = {
        "brand": "Mercedes",
        "model": "EQB",
        "variant": "300",
        "model_year": 2022,
    }

    exact_score = api._score_candidate(exact, "Mercedes", "EQB", "250+", 2024)
    near_score = api._score_candidate(near, "Mercedes", "EQB", "250+", 2024)

    assert exact_score > near_score
    assert exact_score >= 100
