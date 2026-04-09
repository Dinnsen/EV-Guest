from pathlib import Path
root = Path('/mnt/data/ev_guest_package')
files = {}
files['README.md'] = r'''# EV Guest

[![GitHub Release][releases-shield]][releases]
[![GitHub All Releases][download-all-shield]][releases]
[![HACS][hacs-shield]][hacs]

[![BuyMeCoffee][buymecoffee-shield]][buymecoffee]

EV Guest for Home Assistant helps you find the cheapest charging window for guest EVs **without connecting the car to Home Assistant**. The integration fetches vehicle details from a license plate lookup, combines them with a user-selected electricity price sensor, and calculates the cheapest charging plan that respects the desired completion time.

The integration creates local helper entities for guest charging input and result sensors for the final schedule.

> This integration is designed as a custom HACS integration for modern Home Assistant config-entry setup. It uses a user-selected electricity price entity and supports the price attribute format used by Energi Data Service.

## Table of content

- [Installation](#installation)
- [Setup](#setup)
- [Usage](#usage)
- [Entities](#entities)
- [Supported electricity price sensors](#supported-electricity-price-sensors)
- [License plate lookup](#license-plate-lookup)
- [Screenshots](#screenshots)
- [Important notes](#important-notes)
- [Troubleshooting](#troubleshooting)

# Installation:

### Option 1 (easy) - HACS:

- Ensure that HACS is installed.
- Add this repository as a **custom repository** in HACS with category **Integration**.
- Search for and install **EV Guest**.
- Restart Home Assistant.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.][my-ha-badge]][my-ha-url]

### Option 2 - Manual installation:

- Download the latest release.
- Unpack the release and copy the `custom_components/ev_guest` directory into the `custom_components` directory of your Home Assistant installation.
- Restart Home Assistant.

# Setup

My Home Assistant shortcut:

[![Open your Home Assistant instance and start setting up a new integration.][my-ha-add-integration-badge]][my-ha-add-integration-url]

Or go to **Home Assistant > Settings > Devices & Services**.

Add **EV Guest** integration.

### Initial information dialog

During setup, EV Guest asks for:

- **Name**: Friendly name for this integration instance.
- **Electricity Price Sensor**: Select the sensor that exposes current and future electricity prices.
- **Charge Costs Currency**: Select output currency for the cost sensor (`DKK`, `EUR`, `USD`).
- **Clock format**: Choose `24h` or `12h` formatting for start/end sensors.
- **Charge Time format**: Choose `minutes` or `hours_minutes` formatting for the charge time sensor.

# Usage

After setup, the integration exposes helper entities and action buttons.

### Step 1 - Enter the license plate

Fill in the text entity:

- `text.<name>_license_plate`

Then press:

- `button.<name>_grab_car_data`

EV Guest will then try to fetch and populate:

- Car Brand
- Car Model
- Car Variant
- Car Battery Capacity

### Step 2 - Enter charging parameters

Set these helper entities:

- `number.<name>_soc`
- `number.<name>_charger_power`
- `number.<name>_charge_limit`
- `time.<name>_charge_completion_time`

If battery capacity was not found online, you can manually set:

- `number.<name>_battery_capacity`

Then press:

- `button.<name>_calculate`

EV Guest calculates the cheapest charging slot using the selected electricity price sensor and updates the result sensors.

# Entities

## Input/helper entities

### Text

- **License Plate**

### Number

- **SoC** (`%`)
- **Battery Capacity** (`kWh`)
- **Charger Power** (`kW`)
- **Charge Limit** (`%`)

### Time

- **Charge Completion Time**

### Buttons

- **Grab Car Data**
- **Calculate**

## Result sensors

- **Charging Speed** (`%/h`)
- **Charge Start Time**
- **Charge End Time**
- **Charge Time**
- **Charge Costs**
- **Car Brand**
- **Car Model**
- **Car Variant**
- **Car Battery Capacity** (`kWh`)
- **Status**

# Supported electricity price sensors

EV Guest is built to work with sensors that expose hourly prices in attributes. The recommended example is:

- `sensor.energi_data_service`

The integration currently supports these attribute layouts out of the box:

- `raw_today` / `raw_tomorrow` lists of objects with `hour` and `price`
- `today` / `tomorrow` lists of hourly prices for the current and next day
- `forecast` list of objects with `hour` and `price`

This makes it compatible with the common layout used by **Energi Data Service**.

# License plate lookup

EV Guest currently uses this public lookup pattern for vehicle details:

- `https://www.nummerplade.net/nummerplade/<plate>.html`

The integration attempts to extract:

- Brand
- Model
- Variant
- Battery capacity

If the site does not expose battery data for a given vehicle, you can manually set battery capacity in the helper entity.

# Screenshots

Place your screenshots in:

- `docs/screenshots/overview.png`
- `docs/screenshots/setup_step_1.png`
- `docs/screenshots/setup_step_2.png`
- `docs/screenshots/entities.png`

Suggested README section after you add them:

```md
## Screenshots

### Setup
![Setup step 1](docs/screenshots/setup_step_1.png)
![Setup step 2](docs/screenshots/setup_step_2.png)

### Usage
![Overview](docs/screenshots/overview.png)
![Entities](docs/screenshots/entities.png)
```

# Important notes

- EV Guest does **not** control a charger directly.
- EV Guest calculates the cheapest charging window and exposes the result as sensors.
- Vehicle data scraping from third-party sites can change if the site markup changes.
- Currency selection changes only the output unit/currency label. It does **not** perform live FX conversion.
- The integration assumes linear AC charging based on entered charger power and battery capacity.

# Troubleshooting

### Car data not found

- Check that the license plate format is correct.
- Try removing spaces from the plate.
- Some vehicles may not expose battery data online.

### Charge cost looks wrong

- Verify the selected electricity price sensor.
- Check that the sensor provides future hourly prices.
- Confirm that the selected currency matches the price sensor unit.

### No valid charging window found

This usually means one of the following:

- Completion time is too soon.
- Charge limit is below current SoC or already reached.
- Not enough hourly price data is available before the completion deadline.

[releases-shield]: https://img.shields.io/github/release/Dinnsen/EV-Guest.svg?style=for-the-badge
[releases]: https://github.com/Dinnsen/EV-Guest/releases
[download-all-shield]: https://img.shields.io/github/downloads/Dinnsen/EV-Guest/total?style=for-the-badge
[hacs-shield]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge
[hacs]: https://www.hacs.xyz/
[buymecoffee-shield]: https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=000000
[buymecoffee]: https://buymeacoffee.com/dinnsen
[my-ha-badge]: https://my.home-assistant.io/badges/hacs_repository.svg
[my-ha-url]: https://my.home-assistant.io/redirect/hacs_repository/?owner=Dinnsen&repository=EV-Guest&category=integration
[my-ha-add-integration-badge]: https://my.home-assistant.io/badges/config_flow_start.svg
[my-ha-add-integration-url]: https://my.home-assistant.io/redirect/config_flow_start/?domain=ev_guest
'''

files['hacs.json'] = r'''{
  "name": "EV Guest",
  "render_readme": true,
  "homeassistant": "2026.3.0",
  "country": ["DK", "DE", "SE", "NO", "NL", "BE", "FR", "US"],
  "domains": ["ev_guest"],
  "iot_class": "calculated"
}
'''

files['LICENSE'] = r'''MIT License

Copyright (c) 2026 Dinnsen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

files['.gitignore'] = r'''.DS_Store
__pycache__/
*.pyc
*.pyo
*.pytest_cache/
*.mypy_cache/
*.ruff_cache/
venv/
.env
'''

files['.github/workflows/validate.yml'] = r'''name: Validate

on:
  push:
  pull_request:

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install homeassistant beautifulsoup4

      - name: Validate Python syntax
        run: python -m compileall custom_components
'''

files['docs/screenshots/README.md'] = r'''# Screenshot placeholders

Add your screenshots with these file names:

- `overview.png`
- `setup_step_1.png`
- `setup_step_2.png`
- `entities.png`
'''

files['custom_components/ev_guest/__init__.py'] = r'''"""The EV Guest integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import EVGuestCoordinator

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.TEXT,
    Platform.TIME,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EV Guest from a config entry."""
    coordinator = EVGuestCoordinator(hass, entry)
    await coordinator.async_initialize()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: EVGuestCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()
    return unload_ok
'''

files['custom_components/ev_guest/manifest.json'] = r'''{
  "domain": "ev_guest",
  "name": "EV Guest",
  "version": "0.1.0",
  "documentation": "https://github.com/Dinnsen/EV-Guest",
  "issue_tracker": "https://github.com/Dinnsen/EV-Guest/issues",
  "codeowners": ["@Dinnsen"],
  "config_flow": true,
  "iot_class": "calculated",
  "requirements": [
    "beautifulsoup4>=4.12.3"
  ],
  "loggers": ["custom_components.ev_guest"]
}
'''

files['custom_components/ev_guest/const.py'] = r'''"""Constants for EV Guest."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "ev_guest"
DEFAULT_NAME = "EV Guest"
DEFAULT_SCAN_INTERVAL = timedelta(minutes=15)
LOOKUP_BASE_URL = "https://www.nummerplade.net/nummerplade/{plate}.html"
USER_AGENT = "Mozilla/5.0 (compatible; EVGuestHomeAssistant/0.1.0; +https://github.com/Dinnsen/EV-Guest)"

CONF_PRICE_ENTITY = "price_entity"
CONF_CURRENCY = "currency"
CONF_TIME_FORMAT = "time_format"
CONF_DURATION_FORMAT = "duration_format"

TIME_FORMAT_24H = "24h"
TIME_FORMAT_12H = "12h"
DURATION_FORMAT_MINUTES = "minutes"
DURATION_FORMAT_HM = "hours_minutes"

CURRENCIES = ["DKK", "EUR", "USD"]
TIME_FORMATS = [TIME_FORMAT_24H, TIME_FORMAT_12H]
DURATION_FORMATS = [DURATION_FORMAT_MINUTES, DURATION_FORMAT_HM]

ATTR_BRAND = "car_brand"
ATTR_MODEL = "car_model"
ATTR_VARIANT = "car_variant"
ATTR_BATTERY_CAPACITY = "car_battery_capacity"
ATTR_STATUS = "status"
ATTR_LAST_LOOKUP = "last_lookup"
ATTR_LAST_CALCULATION = "last_calculation"

DATA_INPUTS = "inputs"
DATA_RESULTS = "results"

INPUT_LICENSE_PLATE = "license_plate"
INPUT_SOC = "soc"
INPUT_BATTERY_CAPACITY = "battery_capacity"
INPUT_CHARGER_POWER = "charger_power"
INPUT_CHARGE_LIMIT = "charge_limit"
INPUT_CHARGE_COMPLETION_TIME = "charge_completion_time"

RESULT_CHARGING_SPEED = "charging_speed"
RESULT_CHARGE_START_TIME = "charge_start_time"
RESULT_CHARGE_END_TIME = "charge_end_time"
RESULT_CHARGE_TIME = "charge_time"
RESULT_CHARGE_COSTS = "charge_costs"
RESULT_CAR_BRAND = "car_brand"
RESULT_CAR_MODEL = "car_model"
RESULT_CAR_VARIANT = "car_variant"
RESULT_CAR_BATTERY_CAPACITY = "car_battery_capacity"
RESULT_STATUS = "status"
'''

files['custom_components/ev_guest/api.py'] = r'''"""External API helpers for EV Guest."""

from __future__ import annotations

import logging
import re
from typing import Any

from aiohttp import ClientError, ClientSession
from bs4 import BeautifulSoup

from .const import LOOKUP_BASE_URL, USER_AGENT

_LOGGER = logging.getLogger(__name__)


class EVGuestLookupError(Exception):
    """Raised when license plate lookup fails."""


def _clean_plate(plate: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", plate or "").lower()


def _extract_value_from_text(text: str, label: str) -> str | None:
    pattern = rf"{re.escape(label)}\s+(.+?)(?:\n|$)"
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None
    value = match.group(1).strip()
    value = re.sub(r"\s{2,}", " ", value)
    return value or None


def _extract_battery_capacity(text: str) -> float | None:
    patterns = [
        r"Batteri Kapacitet\s+([0-9]+(?:[\.,][0-9]+)?)",
        r"Batterikapacitet\s+([0-9]+(?:[\.,][0-9]+)?)",
        r"Batterikapacitet \(NET\)\s+([0-9]+(?:[\.,][0-9]+)?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(",", "."))
            except ValueError:
                continue
    return None


async def async_lookup_vehicle(session: ClientSession, plate: str) -> dict[str, Any]:
    """Look up vehicle data by license plate."""
    clean_plate = _clean_plate(plate)
    if not clean_plate:
        raise EVGuestLookupError("License plate is empty")

    url = LOOKUP_BASE_URL.format(plate=clean_plate)
    headers = {"User-Agent": USER_AGENT}

    try:
        async with session.get(url, headers=headers, timeout=20) as response:
            if response.status != 200:
                raise EVGuestLookupError(f"Lookup failed with HTTP {response.status}")
            html = await response.text()
    except (TimeoutError, ClientError) as err:
        raise EVGuestLookupError(f"Lookup request failed: {err}") from err

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)

    if "Ukendt fejl" in text and "Mærke" not in text:
        raise EVGuestLookupError("Vehicle page returned an unknown error")

    brand = _extract_value_from_text(text, "Mærke")
    model = _extract_value_from_text(text, "Model")
    variant = _extract_value_from_text(text, "Variant")
    battery_capacity = _extract_battery_capacity(text)

    if not any([brand, model, variant, battery_capacity]):
        _LOGGER.debug("Vehicle lookup page text: %s", text[:5000])
        raise EVGuestLookupError("Could not extract vehicle data from lookup page")

    return {
        "plate": clean_plate.upper(),
        "brand": brand,
        "model": model,
        "variant": variant,
        "battery_capacity": battery_capacity,
        "source_url": url,
    }
'''

files['custom_components/ev_guest/coordinator.py'] = r'''"""Coordinator for EV Guest."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
import logging
from math import ceil
from typing import Any

from aiohttp import ClientSession
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from zoneinfo import ZoneInfo

from .api import EVGuestLookupError, async_lookup_vehicle
from .const import (
    ATTR_LAST_CALCULATION,
    ATTR_LAST_LOOKUP,
    ATTR_STATUS,
    CONF_CURRENCY,
    CONF_DURATION_FORMAT,
    CONF_PRICE_ENTITY,
    CONF_TIME_FORMAT,
    DATA_INPUTS,
    DATA_RESULTS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    DURATION_FORMAT_HM,
    DURATION_FORMAT_MINUTES,
    INPUT_BATTERY_CAPACITY,
    INPUT_CHARGE_COMPLETION_TIME,
    INPUT_CHARGE_LIMIT,
    INPUT_CHARGER_POWER,
    INPUT_LICENSE_PLATE,
    INPUT_SOC,
    RESULT_CAR_BATTERY_CAPACITY,
    RESULT_CAR_BRAND,
    RESULT_CAR_MODEL,
    RESULT_CAR_VARIANT,
    RESULT_CHARGE_COSTS,
    RESULT_CHARGE_END_TIME,
    RESULT_CHARGE_START_TIME,
    RESULT_CHARGE_TIME,
    RESULT_CHARGING_SPEED,
    RESULT_STATUS,
    TIME_FORMAT_12H,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class EVGuestData:
    """Coordinator state."""

    inputs: dict[str, Any]
    results: dict[str, Any]


class EVGuestCoordinator(DataUpdateCoordinator[EVGuestData]):
    """Handle EV Guest data and calculations."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.hass = hass
        self.config_entry = entry
        self.session: ClientSession = async_get_clientsession(hass)
        self._remove_price_listener: CALLBACK_TYPE | None = None
        self.data = EVGuestData(
            inputs={
                INPUT_LICENSE_PLATE: "",
                INPUT_SOC: 20.0,
                INPUT_BATTERY_CAPACITY: 77.0,
                INPUT_CHARGER_POWER: 11.0,
                INPUT_CHARGE_LIMIT: 80.0,
                INPUT_CHARGE_COMPLETION_TIME: time(hour=7, minute=0),
            },
            results={
                RESULT_CHARGING_SPEED: None,
                RESULT_CHARGE_START_TIME: None,
                RESULT_CHARGE_END_TIME: None,
                RESULT_CHARGE_TIME: None,
                RESULT_CHARGE_COSTS: None,
                RESULT_CAR_BRAND: None,
                RESULT_CAR_MODEL: None,
                RESULT_CAR_VARIANT: None,
                RESULT_CAR_BATTERY_CAPACITY: None,
                RESULT_STATUS: "Ready",
                ATTR_LAST_LOOKUP: None,
                ATTR_LAST_CALCULATION: None,
            },
        )

    async def async_initialize(self) -> None:
        """Initialize listeners."""
        price_entity = self.config_entry.data[CONF_PRICE_ENTITY]
        self._remove_price_listener = async_track_state_change_event(
            self.hass,
            [price_entity],
            self._handle_price_update,
        )
        await self.async_refresh()

    async def async_shutdown(self) -> None:
        """Shut down listeners."""
        if self._remove_price_listener:
            self._remove_price_listener()
            self._remove_price_listener = None

    @callback
    def _handle_price_update(self, event: Event) -> None:
        """Recalculate when the electricity price entity changes."""
        self.hass.async_create_task(self.async_calculate())

    async def _async_update_data(self) -> EVGuestData:
        """Refresh coordinator data."""
        return self.data

    async def async_set_input_value(self, key: str, value: Any) -> None:
        """Set an input value and update listeners."""
        self.data.inputs[key] = value
        self.async_update_listeners()

    async def async_lookup_car_data(self) -> None:
        """Look up vehicle details from the configured lookup page."""
        plate = self.data.inputs.get(INPUT_LICENSE_PLATE, "")
        if not plate:
            self.data.results[RESULT_STATUS] = "License plate is required"
            self.async_update_listeners()
            return

        try:
            vehicle = await async_lookup_vehicle(self.session, plate)
        except EVGuestLookupError as err:
            self.data.results[RESULT_STATUS] = f"Lookup failed: {err}"
            self.async_update_listeners()
            return

        self.data.results[RESULT_CAR_BRAND] = vehicle.get("brand")
        self.data.results[RESULT_CAR_MODEL] = vehicle.get("model")
        self.data.results[RESULT_CAR_VARIANT] = vehicle.get("variant")
        self.data.results[RESULT_CAR_BATTERY_CAPACITY] = vehicle.get("battery_capacity")
        self.data.results[ATTR_LAST_LOOKUP] = self._local_now().isoformat()

        if vehicle.get("battery_capacity"):
            self.data.inputs[INPUT_BATTERY_CAPACITY] = float(vehicle["battery_capacity"])

        self.data.results[RESULT_STATUS] = "Vehicle data fetched"
        self.async_update_listeners()

    async def async_calculate(self) -> None:
        """Calculate the cheapest charge schedule."""
        try:
            calculation = self._calculate_schedule()
        except ValueError as err:
            self.data.results[RESULT_STATUS] = str(err)
            self.async_update_listeners()
            return
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("Unexpected calculation error")
            self.data.results[RESULT_STATUS] = f"Calculation failed: {err}"
            self.async_update_listeners()
            return

        self.data.results.update(calculation)
        self.data.results[ATTR_LAST_CALCULATION] = self._local_now().isoformat()
        self.data.results[RESULT_STATUS] = "Calculation complete"
        self.async_update_listeners()

    def _calculate_schedule(self) -> dict[str, Any]:
        soc = float(self.data.inputs[INPUT_SOC])
        battery_capacity = float(self.data.inputs[INPUT_BATTERY_CAPACITY])
        charger_power = float(self.data.inputs[INPUT_CHARGER_POWER])
        charge_limit = float(self.data.inputs[INPUT_CHARGE_LIMIT])
        completion_time: time = self.data.inputs[INPUT_CHARGE_COMPLETION_TIME]

        if battery_capacity <= 0:
            raise ValueError("Battery capacity must be above 0")
        if charger_power <= 0:
            raise ValueError("Charger power must be above 0")
        if not 0 <= soc <= 100:
            raise ValueError("SoC must be between 0 and 100")
        if not 0 <= charge_limit <= 100:
            raise ValueError("Charge limit must be between 0 and 100")
        if charge_limit <= soc:
            raise ValueError("Charge limit must be above current SoC")

        speed_pct_per_hour = (charger_power / battery_capacity) * 100
        energy_needed_kwh = battery_capacity * ((charge_limit - soc) / 100)
        charge_minutes = ceil((energy_needed_kwh / charger_power) * 60)
        required_hours = charge_minutes / 60

        prices = self._extract_price_slots()
        if not prices:
            raise ValueError("No usable price data available from selected price sensor")

        now = self._local_now()
        deadline = self._resolve_deadline(now, completion_time)

        eligible_slots = [slot for slot in prices if now <= slot[0] < deadline]
        if not eligible_slots:
            raise ValueError("No price slots available before completion time")

        slot_count = ceil(required_hours)
        if len(eligible_slots) < slot_count:
            raise ValueError("Not enough hourly price slots before completion time")

        best_window: list[tuple[datetime, float]] | None = None
        best_cost: float | None = None

        for index in range(0, len(eligible_slots) - slot_count + 1):
            window = eligible_slots[index : index + slot_count]
            window_end = window[-1][0] + timedelta(hours=1)
            if window_end > deadline:
                continue

            cost = self._estimate_cost(window, energy_needed_kwh, required_hours)
            if best_cost is None or cost < best_cost:
                best_cost = cost
                best_window = window

        if best_window is None or best_cost is None:
            raise ValueError("No valid charging window found before completion time")

        start = best_window[0][0]
        end = start + timedelta(minutes=charge_minutes)

        return {
            RESULT_CHARGING_SPEED: round(speed_pct_per_hour, 2),
            RESULT_CHARGE_START_TIME: self._format_datetime(start),
            RESULT_CHARGE_END_TIME: self._format_datetime(end),
            RESULT_CHARGE_TIME: self._format_duration(charge_minutes),
            RESULT_CHARGE_COSTS: round(best_cost, 2),
        }

    def _estimate_cost(
        self,
        window: list[tuple[datetime, float]],
        energy_needed_kwh: float,
        required_hours: float,
    ) -> float:
        remaining_energy = energy_needed_kwh
        total_cost = 0.0

        for hour_start, price in window:
            del hour_start
            energy_this_hour = min(self.data.inputs[INPUT_CHARGER_POWER], remaining_energy)
            if remaining_energy < self.data.inputs[INPUT_CHARGER_POWER]:
                energy_this_hour = remaining_energy
            total_cost += energy_this_hour * float(price)
            remaining_energy -= energy_this_hour
            if remaining_energy <= 0:
                break

        # Adjust for partial final hour for better estimate.
        full_hours = int(required_hours)
        partial_hour_fraction = required_hours - full_hours
        if partial_hour_fraction > 0 and len(window) > full_hours:
            last_hour_price = float(window[full_hours][1])
            overcount_energy = self.data.inputs[INPUT_CHARGER_POWER] * (1 - partial_hour_fraction)
            total_cost -= overcount_energy * last_hour_price

        return total_cost

    def _extract_price_slots(self) -> list[tuple[datetime, float]]:
        entity_id = self.config_entry.data[CONF_PRICE_ENTITY]
        state = self.hass.states.get(entity_id)
        if state is None or state.state in {STATE_UNKNOWN, STATE_UNAVAILABLE}:
            raise ValueError("Selected electricity price sensor is unavailable")

        attrs = state.attributes
        timezone = self.hass.config.time_zone or "Europe/Copenhagen"
        tzinfo = ZoneInfo(timezone)

        slots: list[tuple[datetime, float]] = []

        def parse_hourly_dicts(items: list[dict[str, Any]]) -> None:
            for item in items:
                hour_raw = item.get("hour")
                price = item.get("price")
                if hour_raw is None or price is None:
                    continue
                dt = datetime.fromisoformat(hour_raw)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=tzinfo)
                else:
                    dt = dt.astimezone(tzinfo)
                slots.append((dt, float(price)))

        if isinstance(attrs.get("raw_today"), list):
            parse_hourly_dicts(attrs["raw_today"])
        if isinstance(attrs.get("raw_tomorrow"), list):
            parse_hourly_dicts(attrs["raw_tomorrow"])
        if isinstance(attrs.get("forecast"), list):
            parse_hourly_dicts(attrs["forecast"])

        if not slots and isinstance(attrs.get("today"), list):
            base = self._local_now().replace(hour=0, minute=0, second=0, microsecond=0)
            for index, price in enumerate(attrs["today"]):
                slots.append((base + timedelta(hours=index), float(price)))
            if isinstance(attrs.get("tomorrow"), list):
                tomorrow_base = base + timedelta(days=1)
                for index, price in enumerate(attrs["tomorrow"]):
                    slots.append((tomorrow_base + timedelta(hours=index), float(price)))

        deduped: dict[datetime, float] = {}
        for dt, price in sorted(slots, key=lambda item: item[0]):
            deduped[dt] = price

        return sorted(deduped.items(), key=lambda item: item[0])

    def _resolve_deadline(self, now: datetime, completion_time: time) -> datetime:
        deadline = now.replace(
            hour=completion_time.hour,
            minute=completion_time.minute,
            second=0,
            microsecond=0,
        )
        if deadline <= now:
            deadline += timedelta(days=1)
        return deadline

    def _format_datetime(self, value: datetime) -> str:
        if self.config_entry.data[CONF_TIME_FORMAT] == TIME_FORMAT_12H:
            return value.strftime("%I:%M %p")
        return value.strftime("%H:%M")

    def _format_duration(self, total_minutes: int) -> str | int:
        if self.config_entry.data[CONF_DURATION_FORMAT] == DURATION_FORMAT_MINUTES:
            return total_minutes
        hours, minutes = divmod(total_minutes, 60)
        return f"{hours}h {minutes:02d}m"

    def _local_now(self) -> datetime:
        timezone = self.hass.config.time_zone or "Europe/Copenhagen"
        return datetime.now(ZoneInfo(timezone))

    @property
    def currency(self) -> str:
        return self.config_entry.data[CONF_CURRENCY]

    def get_entity_id(self, platform: str, unique_key: str) -> str | None:
        """Get entity_id for a known entity from the registry."""
        registry = er.async_get(self.hass)
        entity_id = registry.async_get_entity_id(platform, DOMAIN, f"{self.config_entry.entry_id}_{unique_key}")
        return entity_id
'''

files['custom_components/ev_guest/config_flow.py'] = r'''"""Config flow for EV Guest."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_CURRENCY,
    CONF_DURATION_FORMAT,
    CONF_PRICE_ENTITY,
    CONF_TIME_FORMAT,
    CURRENCIES,
    DEFAULT_NAME,
    DOMAIN,
    DURATION_FORMATS,
    TIME_FORMATS,
)


class EVGuestConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for EV Guest."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input["name"])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input["name"], data=user_input)

        schema = vol.Schema(
            {
                vol.Required("name", default=DEFAULT_NAME): str,
                vol.Required(CONF_PRICE_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(CONF_CURRENCY, default="DKK"): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=CURRENCIES, mode=selector.SelectSelectorMode.DROPDOWN)
                ),
                vol.Required(CONF_TIME_FORMAT, default="24h"): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=TIME_FORMATS, mode=selector.SelectSelectorMode.DROPDOWN)
                ),
                vol.Required(CONF_DURATION_FORMAT, default="minutes"): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=DURATION_FORMATS, mode=selector.SelectSelectorMode.DROPDOWN)
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry):
        return EVGuestOptionsFlow(config_entry)


class EVGuestOptionsFlow(config_entries.OptionsFlow):
    """Options flow for EV Guest."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {**self.config_entry.data, **self.config_entry.options}
        schema = vol.Schema(
            {
                vol.Required(CONF_PRICE_ENTITY, default=current[CONF_PRICE_ENTITY]): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(CONF_CURRENCY, default=current[CONF_CURRENCY]): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=CURRENCIES, mode=selector.SelectSelectorMode.DROPDOWN)
                ),
                vol.Required(CONF_TIME_FORMAT, default=current[CONF_TIME_FORMAT]): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=TIME_FORMATS, mode=selector.SelectSelectorMode.DROPDOWN)
                ),
                vol.Required(
                    CONF_DURATION_FORMAT,
                    default=current[CONF_DURATION_FORMAT],
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=DURATION_FORMATS, mode=selector.SelectSelectorMode.DROPDOWN)
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
'''

files['custom_components/ev_guest/entity.py'] = r'''"""Entity helpers for EV Guest."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EVGuestCoordinator


class EVGuestCoordinatorEntity(CoordinatorEntity[EVGuestCoordinator], Entity):
    """Base entity for EV Guest."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: EVGuestCoordinator, key: str, name: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_translation_key = key
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.entry_id)},
            name=self.coordinator.config_entry.title,
            manufacturer="Dinnsen",
            model="EV Guest",
            configuration_url="https://github.com/Dinnsen/EV-Guest",
        )
'''

files['custom_components/ev_guest/sensor.py'] = r'''"""Sensor platform for EV Guest."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    RESULT_CAR_BATTERY_CAPACITY,
    RESULT_CAR_BRAND,
    RESULT_CAR_MODEL,
    RESULT_CAR_VARIANT,
    RESULT_CHARGE_COSTS,
    RESULT_CHARGE_END_TIME,
    RESULT_CHARGE_START_TIME,
    RESULT_CHARGE_TIME,
    RESULT_CHARGING_SPEED,
    RESULT_STATUS,
)
from .entity import EVGuestCoordinatorEntity

SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(key=RESULT_CHARGING_SPEED, name="Charging Speed", native_unit_of_measurement="%/h", icon="mdi:speedometer"),
    SensorEntityDescription(key=RESULT_CHARGE_START_TIME, name="Charge Start Time", icon="mdi:clock-start"),
    SensorEntityDescription(key=RESULT_CHARGE_END_TIME, name="Charge End Time", icon="mdi:clock-end"),
    SensorEntityDescription(key=RESULT_CHARGE_TIME, name="Charge Time", icon="mdi:timer-outline"),
    SensorEntityDescription(key=RESULT_CHARGE_COSTS, name="Charge Costs", device_class=SensorDeviceClass.MONETARY, icon="mdi:cash"),
    SensorEntityDescription(key=RESULT_CAR_BRAND, name="Car Brand", entity_category=EntityCategory.DIAGNOSTIC, icon="mdi:car-info"),
    SensorEntityDescription(key=RESULT_CAR_MODEL, name="Car Model", entity_category=EntityCategory.DIAGNOSTIC, icon="mdi:car-info"),
    SensorEntityDescription(key=RESULT_CAR_VARIANT, name="Car Variant", entity_category=EntityCategory.DIAGNOSTIC, icon="mdi:car-info"),
    SensorEntityDescription(key=RESULT_CAR_BATTERY_CAPACITY, name="Car Battery Capacity", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, entity_category=EntityCategory.DIAGNOSTIC, icon="mdi:car-electric"),
    SensorEntityDescription(key=RESULT_STATUS, name="Status", entity_category=EntityCategory.DIAGNOSTIC, icon="mdi:information-outline"),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data["ev_guest"][entry.entry_id]
    async_add_entities(EVGuestSensor(coordinator, description) for description in SENSORS)


class EVGuestSensor(EVGuestCoordinatorEntity, SensorEntity):
    """Representation of an EV Guest sensor."""

    entity_description: SensorEntityDescription

    def __init__(self, coordinator, description: SensorEntityDescription) -> None:
        super().__init__(coordinator, description.key, description.name or description.key)
        self.entity_description = description
        if description.key == RESULT_CHARGE_COSTS:
            self._attr_native_unit_of_measurement = coordinator.currency

    @property
    def native_value(self):
        return self.coordinator.data.results.get(self.entity_description.key)
'''

files['custom_components/ev_guest/button.py'] = r'''"""Button platform for EV Guest."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import EVGuestCoordinatorEntity

BUTTONS = (
    ButtonEntityDescription(key="grab_car_data", name="Grab Car Data", icon="mdi:car-search"),
    ButtonEntityDescription(key="calculate", name="Calculate", icon="mdi:calculator"),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data["ev_guest"][entry.entry_id]
    async_add_entities(EVGuestButton(coordinator, description) for description in BUTTONS)


class EVGuestButton(EVGuestCoordinatorEntity, ButtonEntity):
    """Representation of an EV Guest button."""

    entity_description: ButtonEntityDescription

    def __init__(self, coordinator, description: ButtonEntityDescription) -> None:
        super().__init__(coordinator, description.key, description.name or description.key)
        self.entity_description = description

    async def async_press(self) -> None:
        if self.entity_description.key == "grab_car_data":
            await self.coordinator.async_lookup_car_data()
        elif self.entity_description.key == "calculate":
            await self.coordinator.async_calculate()
'''

files['custom_components/ev_guest/number.py'] = r'''"""Number platform for EV Guest."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfEnergy, UnitOfPower, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    INPUT_BATTERY_CAPACITY,
    INPUT_CHARGE_LIMIT,
    INPUT_CHARGER_POWER,
    INPUT_SOC,
)
from .entity import EVGuestCoordinatorEntity


@dataclass(frozen=True, kw_only=True)
class EVGuestNumberDescription:
    key: str
    name: str
    native_min_value: float
    native_max_value: float
    native_step: float
    native_unit_of_measurement: str | None = None
    icon: str | None = None
    device_class: NumberDeviceClass | None = None
    entity_category: EntityCategory | None = None


NUMBERS = (
    EVGuestNumberDescription(key=INPUT_SOC, name="SoC", native_min_value=0, native_max_value=100, native_step=1, native_unit_of_measurement=PERCENTAGE, icon="mdi:battery-50"),
    EVGuestNumberDescription(key=INPUT_BATTERY_CAPACITY, name="Battery Capacity", native_min_value=1, native_max_value=300, native_step=0.1, native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, icon="mdi:car-electric"),
    EVGuestNumberDescription(key=INPUT_CHARGER_POWER, name="Charger Power", native_min_value=0.1, native_max_value=350, native_step=0.1, native_unit_of_measurement=UnitOfPower.KILO_WATT, icon="mdi:ev-station"),
    EVGuestNumberDescription(key=INPUT_CHARGE_LIMIT, name="Charge Limit", native_min_value=0, native_max_value=100, native_step=1, native_unit_of_measurement=PERCENTAGE, icon="mdi:battery-arrow-up"),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data["ev_guest"][entry.entry_id]
    async_add_entities(EVGuestNumber(coordinator, description) for description in NUMBERS)


class EVGuestNumber(EVGuestCoordinatorEntity, NumberEntity):
    """Representation of an EV Guest number entity."""

    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator, description: EVGuestNumberDescription) -> None:
        super().__init__(coordinator, description.key, description.name)
        self.entity_description = description
        self._attr_native_min_value = description.native_min_value
        self._attr_native_max_value = description.native_max_value
        self._attr_native_step = description.native_step
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_icon = description.icon
        self._attr_device_class = description.device_class
        self._attr_entity_category = description.entity_category

    @property
    def native_value(self):
        return self.coordinator.data.inputs.get(self._key)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_input_value(self._key, float(value))
'''

files['custom_components/ev_guest/text.py'] = r'''"""Text platform for EV Guest."""

from __future__ import annotations

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import INPUT_LICENSE_PLATE
from .entity import EVGuestCoordinatorEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data["ev_guest"][entry.entry_id]
    async_add_entities([EVGuestText(coordinator)])


class EVGuestText(EVGuestCoordinatorEntity, TextEntity):
    """Representation of the EV Guest license plate text entity."""

    _attr_mode = TextMode.TEXT
    _attr_icon = "mdi:card-text-outline"
    _attr_native_max = 16

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, INPUT_LICENSE_PLATE, "License Plate")

    @property
    def native_value(self) -> str:
        return self.coordinator.data.inputs.get(self._key, "")

    async def async_set_value(self, value: str) -> None:
        await self.coordinator.async_set_input_value(self._key, value)
'''

files['custom_components/ev_guest/time.py'] = r'''"""Time platform for EV Guest."""

from __future__ import annotations

from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import INPUT_CHARGE_COMPLETION_TIME
from .entity import EVGuestCoordinatorEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data["ev_guest"][entry.entry_id]
    async_add_entities([EVGuestCompletionTime(coordinator)])


class EVGuestCompletionTime(EVGuestCoordinatorEntity, TimeEntity):
    """Representation of the EV Guest completion time entity."""

    _attr_icon = "mdi:clock-check-outline"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, INPUT_CHARGE_COMPLETION_TIME, "Charge Completion Time")

    @property
    def native_value(self) -> time:
        return self.coordinator.data.inputs[self._key]

    async def async_set_value(self, value: time) -> None:
        await self.coordinator.async_set_input_value(self._key, value)
'''

files['custom_components/ev_guest/strings.json'] = r'''{
  "config": {
    "step": {
      "user": {
        "title": "EV Guest",
        "description": "Set up EV Guest.",
        "data": {
          "name": "Name",
          "price_entity": "Electricity price sensor",
          "currency": "Charge costs currency",
          "time_format": "Clock format",
          "duration_format": "Charge time format"
        }
      }
    },
    "options": {
      "step": {
        "init": {
          "title": "EV Guest options",
          "data": {
            "price_entity": "Electricity price sensor",
            "currency": "Charge costs currency",
            "time_format": "Clock format",
            "duration_format": "Charge time format"
          }
        }
      }
    }
  },
  "entity": {
    "button": {
      "grab_car_data": {"name": "Grab Car Data"},
      "calculate": {"name": "Calculate"}
    },
    "number": {
      "soc": {"name": "SoC"},
      "battery_capacity": {"name": "Battery Capacity"},
      "charger_power": {"name": "Charger Power"},
      "charge_limit": {"name": "Charge Limit"}
    },
    "sensor": {
      "charging_speed": {"name": "Charging Speed"},
      "charge_start_time": {"name": "Charge Start Time"},
      "charge_end_time": {"name": "Charge End Time"},
      "charge_time": {"name": "Charge Time"},
      "charge_costs": {"name": "Charge Costs"},
      "car_brand": {"name": "Car Brand"},
      "car_model": {"name": "Car Model"},
      "car_variant": {"name": "Car Variant"},
      "car_battery_capacity": {"name": "Car Battery Capacity"},
      "status": {"name": "Status"}
    },
    "text": {
      "license_plate": {"name": "License Plate"}
    },
    "time": {
      "charge_completion_time": {"name": "Charge Completion Time"}
    }
  }
}
'''

files['custom_components/ev_guest/translations/en.json'] = files['custom_components/ev_guest/strings.json']
files['custom_components/ev_guest/translations/da.json'] = r'''{
  "config": {
    "step": {
      "user": {
        "title": "EV Guest",
        "description": "Opsæt EV Guest.",
        "data": {
          "name": "Navn",
          "price_entity": "Elprissensor",
          "currency": "Valuta for ladeomkostninger",
          "time_format": "Tidsformat",
          "duration_format": "Format for ladetid"
        }
      }
    },
    "options": {
      "step": {
        "init": {
          "title": "EV Guest indstillinger",
          "data": {
            "price_entity": "Elprissensor",
            "currency": "Valuta for ladeomkostninger",
            "time_format": "Tidsformat",
            "duration_format": "Format for ladetid"
          }
        }
      }
    }
  },
  "entity": {
    "button": {
      "grab_car_data": {"name": "Hent bildata"},
      "calculate": {"name": "Beregn"}
    },
    "number": {
      "soc": {"name": "SoC"},
      "battery_capacity": {"name": "Batterikapacitet"},
      "charger_power": {"name": "Ladeeffekt"},
      "charge_limit": {"name": "Ladegrænse"}
    },
    "sensor": {
      "charging_speed": {"name": "Ladehastighed"},
      "charge_start_time": {"name": "Ladestart"},
      "charge_end_time": {"name": "Ladeslut"},
      "charge_time": {"name": "Ladetid"},
      "charge_costs": {"name": "Ladeomkostninger"},
      "car_brand": {"name": "Bilfabrikat"},
      "car_model": {"name": "Bilmodel"},
      "car_variant": {"name": "Bilvariant"},
      "car_battery_capacity": {"name": "Bilens batterikapacitet"},
      "status": {"name": "Status"}
    },
    "text": {
      "license_plate": {"name": "Nummerplade"}
    },
    "time": {
      "charge_completion_time": {"name": "Færdig ladet kl."}
    }
  }
}
'''

files['custom_components/ev_guest/brand/logo.svg'] = r'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" role="img" aria-label="EV Guest logo">
  <rect width="256" height="256" rx="48" fill="#0f172a"/>
  <path d="M58 84h74l-14 24H86v18h30l-14 24H58V84zm92 0h26c23 0 42 19 42 42s-19 42-42 42h-26V84zm26 60c10 0 18-8 18-18s-8-18-18-18h-2v36h2z" fill="#e2e8f0"/>
  <path d="M116 196l28-44h-18l42-52-14 36h18l-32 60z" fill="#22c55e"/>
</svg>
'''
files['custom_components/ev_guest/brand/icon.svg'] = files['custom_components/ev_guest/brand/logo.svg']

for path, content in files.items():
    full = root / path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding='utf-8')
print(f'Wrote {len(files)} files')
