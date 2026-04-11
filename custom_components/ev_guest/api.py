"""API helpers for EV Guest."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import re
from difflib import SequenceMatcher
from typing import Any

from aiohttp import ClientError, ClientSession

from .const import (
    COUNTRY_DK,
    COUNTRY_PROVIDER_DEFAULTS,
    MOTORAPI_BASE_URL,
    NHTSA_DECODE_URL,
    OPEN_EV_DATA_FALLBACK_URL,
    OPEN_EV_DATA_URL,
    PLATE_PROVIDER_MOTORAPI_DK,
    USER_AGENT,
)

_LOGGER = logging.getLogger(__name__)


class EVGuestError(Exception):
    """Base EV Guest exception."""


class EVGuestAuthError(EVGuestError):
    """Authentication error."""


class EVGuestLookupError(EVGuestError):
    """Lookup error."""


@dataclass(slots=True)
class VehicleLookupResult:
    """Normalized vehicle result."""

    plate: str
    vin: str | None
    brand: str | None
    model: str | None
    variant: str | None
    model_year: int | None
    fuel_type: str | None
    source: str
    raw: dict[str, Any]


@dataclass(slots=True)
class BatteryLookupResult:
    """Battery lookup result."""

    battery_capacity: float | None
    source: str
    match_score: float | None
    raw: dict[str, Any] | None


def clean_identifier(value: str) -> str:
    """Normalize plate/VIN strings."""
    return re.sub(r"[^A-Za-z0-9]", "", value or "").upper()


def normalize_text(value: str | None) -> str:
    """Normalize free text for matching."""
    if not value:
        return ""
    return re.sub(r"[^a-z0-9+]", "", value.lower())


def _extract_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"([0-9]+(?:[\.,][0-9]+)?)", value)
        if match:
            return float(match.group(1).replace(",", "."))
    return None


def get_default_plate_provider(country: str) -> str:
    """Return the default plate provider for a country."""
    return COUNTRY_PROVIDER_DEFAULTS.get(country, PLATE_PROVIDER_MOTORAPI_DK)


async def async_validate_country_provider_credentials(
    session: ClientSession, country: str, api_key: str
) -> None:
    """Validate provider credentials for the selected country."""
    provider = get_default_plate_provider(country)
    if provider == PLATE_PROVIDER_MOTORAPI_DK:
        await async_validate_motorapi_key(session, api_key)
        return
    raise EVGuestLookupError("unsupported_country")


async def async_lookup_vehicle_by_country(
    session: ClientSession, plate: str, country: str, api_key: str
) -> VehicleLookupResult:
    """Look up vehicle data for the selected country."""
    provider = get_default_plate_provider(country)
    if provider == PLATE_PROVIDER_MOTORAPI_DK and country == COUNTRY_DK:
        return await async_lookup_vehicle_motorapi(session, plate, api_key)
    raise EVGuestLookupError("unsupported_country")


async def async_validate_motorapi_key(session: ClientSession, api_key: str) -> None:
    """Validate the MotorAPI key with a harmless request."""
    if not api_key:
        raise EVGuestAuthError("missing_api_key")
    url = f"{MOTORAPI_BASE_URL}/vehicles/AA00000"
    headers = {"User-Agent": USER_AGENT, "X-AUTH-TOKEN": api_key}
    try:
        async with session.get(url, headers=headers, timeout=20) as resp:
            if resp.status == 401:
                raise EVGuestAuthError("invalid_auth")
            if resp.status in (200, 404):
                return
            raise EVGuestLookupError(f"unexpected_http_{resp.status}")
    except ClientError as err:
        raise EVGuestLookupError("cannot_connect") from err
    except TimeoutError as err:
        raise EVGuestLookupError("timeout") from err


async def async_lookup_vehicle_motorapi(
    session: ClientSession, plate: str, api_key: str
) -> VehicleLookupResult:
    """Look up vehicle data using MotorAPI."""
    plate = clean_identifier(plate)
    if not plate:
        raise EVGuestLookupError("empty_plate")
    if not api_key:
        raise EVGuestAuthError("missing_api_key")

    url = f"{MOTORAPI_BASE_URL}/vehicles/{plate}"
    headers = {"User-Agent": USER_AGENT, "X-AUTH-TOKEN": api_key}
    try:
        async with session.get(url, headers=headers, timeout=20) as resp:
            if resp.status == 401:
                raise EVGuestAuthError("invalid_auth")
            if resp.status == 404:
                raise EVGuestLookupError("vehicle_not_found")
            if resp.status != 200:
                raise EVGuestLookupError(f"unexpected_http_{resp.status}")
            data = await resp.json()
    except ClientError as err:
        raise EVGuestLookupError("cannot_connect") from err
    except TimeoutError as err:
        raise EVGuestLookupError("timeout") from err

    return VehicleLookupResult(
        plate=plate,
        vin=data.get("vin"),
        brand=data.get("make") or data.get("brand"),
        model=data.get("model"),
        variant=data.get("variant") or data.get("version") or data.get("type_name"),
        model_year=_extract_year(data.get("model_year")),
        fuel_type=data.get("fuel_type"),
        source="MotorAPI",
        raw=data,
    )


async def async_decode_vin_nhtsa(
    session: ClientSession, vin: str, model_year: int | None = None
) -> VehicleLookupResult | None:
    """Decode a VIN using NHTSA vPIC."""
    vin = clean_identifier(vin)
    if not vin:
        return None

    url = NHTSA_DECODE_URL.format(vin=vin)
    if model_year:
        url += f"&modelyear={model_year}"

    try:
        async with session.get(url, headers={"User-Agent": USER_AGENT}, timeout=20) as resp:
            if resp.status != 200:
                return None
            payload = await resp.json()
    except (ClientError, TimeoutError):
        return None

    results = payload.get("Results") if isinstance(payload, dict) else None
    if not isinstance(results, list) or not results:
        return None

    row = results[0]
    if not isinstance(row, dict):
        return None

    return VehicleLookupResult(
        plate="",
        vin=vin,
        brand=row.get("Make") or row.get("Manufacturer"),
        model=row.get("Model"),
        variant=row.get("Trim") or row.get("Series"),
        model_year=_extract_year(row.get("ModelYear")) or model_year,
        fuel_type=row.get("FuelTypePrimary"),
        source="NHTSA vPIC",
        raw=row,
    )


async def async_lookup_battery_open_ev_data(
    session: ClientSession,
    brand: str | None,
    model: str | None,
    variant: str | None,
    model_year: int | None,
) -> BatteryLookupResult:
    """Look up battery data in Open EV Data."""
    dataset = await _async_fetch_open_ev_dataset(session)
    candidates = _extract_candidates(dataset)
    if not candidates:
        return BatteryLookupResult(None, "Open EV Data", None, None)

    scored = sorted(
        (
            (_score_candidate(item, brand, model, variant, model_year), item)
            for item in candidates
        ),
        key=lambda item: item[0],
        reverse=True,
    )
    best_score, best = scored[0]
    if best_score < 45:
        return BatteryLookupResult(None, "Open EV Data", best_score, best)
    return BatteryLookupResult(best.get("battery_capacity"), "Open EV Data", best_score, best)


async def _async_fetch_open_ev_dataset(session: ClientSession) -> Any:
    for url in (OPEN_EV_DATA_URL, OPEN_EV_DATA_FALLBACK_URL):
        try:
            async with session.get(url, headers={"User-Agent": USER_AGENT}, timeout=30) as resp:
                if resp.status == 200:
                    return await resp.json(content_type=None)
        except (ClientError, TimeoutError):
            _LOGGER.debug("Could not fetch Open EV Data from %s", url)
    return []


def _extract_year(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _extract_candidates(node: Any, inherited_brand: str | None = None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if isinstance(node, list):
        for child in node:
            items.extend(_extract_candidates(child, inherited_brand=inherited_brand))
        return items
    if not isinstance(node, dict):
        return items

    brand = node.get("brand") or node.get("make") or inherited_brand
    model = node.get("model") or (
        node.get("name") if node.get("battery") or node.get("variant") else None
    )
    variant = node.get("variant") or node.get("trim") or node.get("version")
    year = _extract_year(node.get("model_year") or node.get("release_year") or node.get("year"))

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
        battery = _extract_float(node.get(key))
        if battery is not None:
            break

    if battery is None and isinstance(node.get("battery"), dict):
        battery = (
            _extract_float(node["battery"].get("usable_kwh"))
            or _extract_float(node["battery"].get("usable"))
            or _extract_float(node["battery"].get("nominal_kwh"))
            or _extract_float(node["battery"].get("capacity"))
        )

    if brand and model and battery is not None:
        items.append(
            {
                "brand": brand,
                "model": model,
                "variant": variant,
                "model_year": year,
                "battery_capacity": battery,
            }
        )

    for value in node.values():
        if isinstance(value, (list, dict)):
            items.extend(_extract_candidates(value, inherited_brand=brand))
    return items


def _score_candidate(
    candidate: dict[str, Any],
    brand: str | None,
    model: str | None,
    variant: str | None,
    model_year: int | None,
) -> float:
    score = 0.0
    cand_brand = normalize_text(candidate.get("brand"))
    cand_model = normalize_text(candidate.get("model"))
    cand_variant = normalize_text(candidate.get("variant"))

    brand_n = normalize_text(brand)
    model_n = normalize_text(model)
    variant_n = normalize_text(variant)

    if brand_n and cand_brand:
        score += 35 if brand_n == cand_brand else 15 * SequenceMatcher(None, brand_n, cand_brand).ratio()
    if model_n and cand_model:
        score += 40 if model_n == cand_model else 18 * SequenceMatcher(None, model_n, cand_model).ratio()
    if variant_n and cand_variant:
        if variant_n == cand_variant:
            score += 30
        elif variant_n in cand_variant or cand_variant in variant_n:
            score += 24
        else:
            score += 12 * SequenceMatcher(None, variant_n, cand_variant).ratio()
    elif not variant_n:
        score += 8

    cand_year = candidate.get("model_year")
    if model_year and cand_year:
        if model_year == cand_year:
            score += 10
        elif abs(model_year - cand_year) <= 1:
            score += 6
    return score
