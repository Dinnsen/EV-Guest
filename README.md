# EV Guest

[![GitHub Release][releases-shield]][releases]
[![GitHub All Releases][download-all-shield]][releases]
[![HACS][hacs-shield]][hacs]
[![BuyMeCoffee][buymecoffee-shield]][buymecoffee]

EV Guest for Home Assistant helps you find the cheapest charging window for guest EVs **without connecting the car to Home Assistant**.

The integration:
- looks up vehicle identity from the guest's license plate
- enriches vehicle data from the VIN when available
- matches the vehicle against Open EV Data to estimate battery capacity
- combines the result with a user-selected electricity price sensor to calculate the cheapest charging plan before a chosen completion time

This package is built as a **Silver-aligned custom integration**. That means the package includes UI setup, unload support, reauthentication, entity availability handling, explicit parallel update settings, service actions, and diagnostics. The official Home Assistant Integration Quality Scale itself only applies to integrations that are reviewed in core, so this repository is **aligned with Silver requirements**, not officially certified as Silver. Home Assistant’s quality scale defines Silver as Bronze plus config-entry unloading, marking entities unavailable when appropriate, logging unavailable/back-connected events, parallel-update limits, UI reauthentication, and over 95% test coverage. citeturn549688view0

## Table of content
- [Installation](#installation)
- [Setup](#setup)
- [Configuration options](#configuration-options)
- [Usage](#usage)
- [Entities](#entities)
- [Service actions](#service-actions)
- [Supported electricity price sensors](#supported-electricity-price-sensors)
- [Data update behavior](#data-update-behavior)
- [Screenshots](#screenshots)
- [Legal information](#legal-information)
- [Known limitations](#known-limitations)
- [Troubleshooting](#troubleshooting)
- [Removal](#removal)

# Installation

### Option 1 - HACS
- Ensure HACS is installed.
- Add this repository as a **custom repository** in HACS with category **Integration**.
- Install **EV Guest**.
- Restart Home Assistant.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.][my-ha-badge]][my-ha-url]

### Option 2 - Manual
- Download the latest release.
- Copy `custom_components/ev_guest` into your Home Assistant `custom_components` folder.
- Restart Home Assistant.

# Setup

Add **EV Guest** from **Settings → Devices & Services**.

During setup, EV Guest asks for:
- **Name**
- **Electricity Price Sensor**
- **Charge Costs Currency** (`DKK`, `EUR`, `USD`)
- **Clock format** (`24h` or `12h`)
- **Charge Time format** (`minutes` or `hours_minutes`)
- **MotorAPI API key**

The integration tests the MotorAPI key during setup and reauthentication. Config-flow setup through the UI and connection testing are both part of the quality-scale rules for Bronze, while Silver adds a UI reauthentication flow. citeturn549688view0

No user setup is needed for:
- **NHTSA vPIC**
- **Open EV Data**

# Configuration options

After setup, the options flow lets you change:
- Electricity Price Sensor
- Charge Costs Currency
- Clock format
- Charge Time format
- MotorAPI API key

# Usage

1. Enter the plate in the license-plate text entity.
2. Press **Grab Car Data**.
3. Review the returned brand, model, variant, and battery estimate.
4. Set SoC, charger power, charge limit, and completion time.
5. Press **Calculate**.

If the online battery match is weak, set battery capacity manually and calculate again.

# Entities

## Input/helper entities
- License Plate
- SoC
- Battery Capacity
- Charger Power
- Charge Limit
- Charge Completion Time
- Grab Car Data
- Calculate

## Result sensors
- Charging Speed
- Charge Start Time
- Charge End Time
- Charge Time
- Charge Costs
- Car Brand
- Car Model
- Car Variant
- Car Battery Capacity
- Status

## Availability
Vehicle-data result sensors are marked unavailable if the upstream lookup is unavailable, matching the Silver rule for marking entities unavailable when appropriate. citeturn549688view0

# Service actions

EV Guest registers two service actions during integration setup:
- `ev_guest.grab_car_data`
- `ev_guest.calculate`

Both require `entry_id`.

Example:
```yaml
service: ev_guest.calculate
data:
  entry_id: 1234567890abcdef
```

# Supported electricity price sensors

EV Guest works with sensors exposing hourly prices in one of these layouts:
- `raw_today` / `raw_tomorrow` with `hour` + `price`
- `today` / `tomorrow` hourly arrays
- `forecast` with `hour` + `price`

The example sensor `sensor.energi_data_service` fits this pattern.

# Data update behavior

EV Guest listens for state changes on the selected electricity-price sensor and recalculates when needed. It also keeps a coordinator with a 30-minute refresh interval for internal state handling. Home Assistant’s diagnostics documentation also describes that integrations can expose redacted config-entry diagnostics for troubleshooting, which this package includes. citeturn549688view1

# Screenshots

Place screenshots here:
- `docs/screenshots/overview.png`
- `docs/screenshots/setup_step_1.png`
- `docs/screenshots/setup_step_2.png`
- `docs/screenshots/entities.png`

# Legal information

EV Guest is **not affiliated with, endorsed by, or maintained by** Home Assistant, MotorAPI, NHTSA, or Open EV Data.

Third-party sources used:
- MotorAPI for Danish license plate and VIN lookup
- NHTSA vPIC for VIN decoding fallback
- Open EV Data for battery matching

Open EV Data attribution is included in this repository as required by that dataset’s license terms. The diagnostics docs also stress that passwords, API keys, tokens, location data, and personal information must not be exposed, which is why EV Guest redacts API key, VIN, and plate data in diagnostics. citeturn549688view1

License plates, VINs, and derived vehicle metadata may be sent to external services while lookups are performed. Users are responsible for their own API keys and third-party service usage.

# Known limitations

- Battery matching is best effort.
- Some variants differ across years and markets.
- Currency selection changes the unit label only; it does not perform FX conversion.
- Charging is calculated as a linear AC session from user-supplied charger power.
- The package includes a tests folder and Silver-oriented structure, but I have not executed a Home Assistant test suite here, so I cannot honestly claim verified 95% test coverage yet.

# Troubleshooting

### Car data not found
- Check the plate format.
- Check the MotorAPI key.
- Some cars may not have a confident battery match.

### Sensors unavailable
- The external lookup service may be down.
- Reauthenticate the integration if the MotorAPI key has changed.

### Charge cost looks wrong
- Confirm the selected electricity price sensor.
- Confirm future hourly prices are present.
- Confirm battery capacity and charger power.

# Removal

To remove EV Guest:
- Go to **Settings → Devices & Services**
- Open **EV Guest**
- Choose **Delete**
- Restart Home Assistant if you installed it manually and want to remove the files from `custom_components`

[releases-shield]: https://img.shields.io/github/release/Dinnsen/EV-Guest.svg?style=for-the-badge
[releases]: https://github.com/Dinnsen/EV-Guest/releases
[download-all-shield]: https://img.shields.io/github/downloads/Dinnsen/EV-Guest/total?style=for-the-badge
[hacs-shield]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge
[hacs]: https://www.hacs.xyz/
[buymecoffee-shield]: https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=000000
[buymecoffee]: https://buymeacoffee.com/dinnsen
[my-ha-badge]: https://my.home-assistant.io/badges/hacs_repository.svg
[my-ha-url]: https://my.home-assistant.io/redirect/hacs_repository/?owner=Dinnsen&repository=EV-Guest&category=integration

## Changelog

### v0.3.1
- Added missing input entities for SoC, Charger Power, Charge Limit, completion time and completion toggle.
- Reworked completion time input to follow the selected 12h/24h format.
- Fixed options/configure flow.
- Fixed local brand images by shipping PNG assets.
- Added tests to the package.
