"""External API helpers for EV Guest."""

from __future__ import annotations

import logging
import re
from difflib import SequenceMatcher
from typing import Any

from aiohttp import ClientError, ClientSession

from .const import MOTORAPI_BASE_URL, NHTSA_DECODE_URL, OPEN_EV_DATA_URL, USER_AGENT

_LOGGER = logging.getLogger(__name__)


class EVGuestLookupError(Exception):
    """Raised when vehicle lookup fails."""


def _clean_plate(plate: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", plate or "").upper()


def _normalize(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"[^a-z0-9+]", "", text.lower())


def _coerce_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"([0-9]+(?:[\.,][0-9]+)?)", value)
        if match:
            try:
                return float(match.group(1).replace(",", "."))
            except ValueError:
                return None
    return None


async def async_lookup_vehicle_motorapi(session: ClientSession, plate: str, api_key: str) -> dict[str, Any]:
    """Look up vehicle data by license plate using MotorAPI."""
    clean_plate = _clean_plate(plate)
    if not clean_plate:
        raise EVGuestLookupError("License plate is empty")
    if not api_key:
        raise EVGuestLookupError("MotorAPI key is missing")

    url = f"{MOTORAPI_BASE_URL}/vehicles/{clean_plate}"
    headers = {"User-Agent": USER_AGENT, "X-AUTH-TOKEN": api_key}

    try:
        async with session.get(url, headers=headers, timeout=20) as response:
            if response.status == 401:
                raise EVGuestLookupError("MotorAPI authentication failed")
            if response.status == 404:
                raise EVGuestLookupError("Vehicle not found in MotorAPI")
            if response.status != 200:
                raise EVGuestLookupError(f"MotorAPI lookup failed with HTTP {response.status}")
            data = await response.json()
    except (TimeoutError, ClientError) as err:
        raise EVGuestLookupError(f"MotorAPI request failed: {err}") from err

    if not isinstance(data, dict):
        raise EVGuestLookupError("MotorAPI returned unexpected data")

    return {
        "plate": clean_plate,
        "vin": data.get("vin"),
        "brand": data.get("make"),
        "model": data.get("model"),
        "variant": data.get("variant"),
        "model_year": data.get("model_year"),
        "fuel_type": data.get("fuel_type"),
        "source": "MotorAPI",
        "raw": data,
    }


async def async_decode_vin_nhtsa(session: ClientSession, vin: str, model_year: int | None = None) -> dict[str, Any]:
    """Decode VIN using the public NHTSA vPIC endpoint."""
    vin = _clean_plate(vin)
    if not vin:
        return {}

    url = NHTSA_DECODE_URL.format(vin=vin)
    if model_year:
        url = f"{url}&modelyear={model_year}"
    headers = {"User-Agent": USER_AGENT}

    try:
        async with session.get(url, headers=headers, timeout=20) as response:
            if response.status != 200:
                return {}
            payload = await response.json()
    except (TimeoutError, ClientError):
        return {}

    results = payload.get("Results") if isinstance(payload, dict) else None
    if not isinstance(results, list) or not results:
        return {}
    result = results[0]
    if not isinstance(result, dict):
        return {}

    return {
        "vin": vin,
        "brand": result.get("Make") or result.get("Manufacturer"),
        "model": result.get("Model"),
        "variant": result.get("Trim") or result.get("Series"),
        "model_year": result.get("ModelYear") or model_year,
        "fuel_type": result.get("FuelTypePrimary"),
        "source": "NHTSA vPIC",
        "raw": result,
    }


def _extract_candidate_records(node: Any, inherited_brand: str | None = None) -> list[dict[str, Any]]:
    """Extract best-effort vehicle records from multiple Open EV Data shapes."""
    candidates: list[dict[str, Any]] = []
    if isinstance(node, list):
        for item in node:
            candidates.extend(_extract_candidate_records(item, inherited_brand=inherited_brand))
        return candidates

    if not isinstance(node, dict):
        return candidates

    brand = node.get("brand") or node.get("make") or inherited_brand
    if isinstance(node.get("name"), str) and brand is None and node.get("models"):
        brand = node.get("name")

    model = node.get("model") or node.get("name") if node.get("variant") or node.get("battery") else node.get("model")
    variant = node.get("variant") or node.get("trim") or node.get("version")
    year = node.get("model_year") or node.get("release_year") or node.get("year")

    battery = None
    for key in (
        "battery_capacity",
        "battery_capacity_kwh",
        "usable_battery_size",
        "usable_battery_capacity",
        "nominal_battery_capacity",
        "battery_size",
        "usable_kwh",
        "battery_kwh",
    ):
        battery = _coerce_float(node.get(key))
        if battery is not None:
            break

    if battery is None and isinstance(node.get("battery"), dict):
        batt = node["battery"]
        for key in (
            "usable_kwh",
            "usable",
            "nominal_kwh",
            "nominal",
            "capacity",
            "net_capacity",
            "gross_capacity",
        ):
            battery = _coerce_float(batt.get(key))
            if battery is not None:
                break

    if (brand or inherited_brand) and model and battery is not None:
        candidates.append({
            "brand": brand or inherited_brand,
            "model": model,
            "variant": variant,
            "model_year": year,
            "battery_capacity": battery,
            "source": "Open EV Data",
        })

    for key, value in node.items():
        next_brand = brand
        if key in {"brands", "models", "vehicles", "data", "results"}:
            candidates.extend(_extract_candidate_records(value, inherited_brand=next_brand))
        elif isinstance(value, (list, dict)):
            candidates.extend(_extract_candidate_records(value, inherited_brand=next_brand))
    return candidates


def _score_candidate(candidate: dict[str, Any], brand: str | None, model: str | None, variant: str | None, model_year: int | None) -> float:
    score = 0.0
    cand_brand = _normalize(candidate.get("brand"))
    cand_model = _normalize(candidate.get("model"))
    cand_variant = _normalize(candidate.get("variant"))
    brand_n = _normalize(brand)
    model_n = _normalize(model)
    variant_n = _normalize(variant)

    if brand_n and cand_brand:
        if brand_n == cand_brand:
            score += 40
        else:
            score += 20 * SequenceMatcher(None, brand_n, cand_brand).ratio()
    if model_n and cand_model:
        if model_n == cand_model:
            score += 40
        else:
            score += 20 * SequenceMatcher(None, model_n, cand_model).ratio()
    if variant_n and cand_variant:
        if variant_n == cand_variant:
            score += 30
        elif variant_n in cand_variant or cand_variant in variant_n:
            score += 22
        else:
            score += 15 * SequenceMatcher(None, variant_n, cand_variant).ratio()
    elif not variant_n:
        score += 5

    cand_year = candidate.get("model_year")
    try:
        cand_year = int(cand_year) if cand_year is not None else None
    except (TypeError, ValueError):
        cand_year = None
    if model_year and cand_year:
        if model_year == cand_year:
            score += 10
        elif abs(model_year - cand_year) <= 1:
            score += 5
    return score


async def async_lookup_battery_open_ev_data(
    session: ClientSession,
    *,
    brand: str | None,
    model: str | None,
    variant: str | None,
    model_year: int | None = None,
) -> dict[str, Any]:
    """Look up battery data from Open EV Data using best-effort matching."""
    headers = {"User-Agent": USER_AGENT}
    try:
        async with session.get(OPEN_EV_DATA_URL, headers=headers, timeout=25) as response:
            if response.status != 200:
                return {}
            payload = await response.json()
    except (TimeoutError, ClientError):
        return {}

    candidates = _extract_candidate_records(payload)
    if not candidates:
        _LOGGER.debug("Open EV Data returned no parsable candidates")
        return {}

    ranked = sorted(
        candidates,
        key=lambda item: _score_candidate(item, brand, model, variant, model_year),
        reverse=True,
    )
    best = ranked[0]
    best_score = _score_candidate(best, brand, model, variant, model_year)
    if best_score < 45:
        return {}
    return best
