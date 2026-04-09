# EV Guest

[![GitHub Release][releases-shield]][releases]
[![GitHub All Releases][download-all-shield]][releases]
[![HACS][hacs-shield]][hacs]
[![BuyMeCoffee][buymecoffee-shield]][buymecoffee]

EV Guest for Home Assistant helps you find the cheapest charging window for guest EVs **without connecting the car to Home Assistant**.

The integration:
- looks up vehicle identity from the guest's license plate
- validates and enriches vehicle data from the VIN when available
- matches the vehicle against an open EV dataset to estimate battery capacity
- combines the result with a user-selected electricity price sensor to calculate the cheapest charging plan before a chosen completion time

The integration creates local helper entities for guest charging input and result sensors for the final schedule.

> EV Guest is a custom HACS integration for modern Home Assistant config-entry setup. It is designed to work with external electricity-price entities such as Energi Data Service.

## Table of content

- [Installation](#installation)
- [Setup](#setup)
- [Usage](#usage)
- [Entities](#entities)
- [Supported electricity price sensors](#supported-electricity-price-sensors)
- [Vehicle lookup flow](#vehicle-lookup-flow)
- [Screenshots](#screenshots)
- [Legal information](#legal-information)
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
- **MotorAPI API key**: Used for Danish license plate and VIN lookup.

No user setup is needed for the built-in **NHTSA vPIC** fallback or **Open EV Data** battery lookup.

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

If battery capacity was not matched online, you can manually set:

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

This makes it compatible with the common layout used by **Energi Data Service** and similar price sensors.

# Vehicle lookup flow

EV Guest uses this lookup order:

1. **MotorAPI** for license plate → vehicle details + VIN
2. **NHTSA vPIC** for VIN decoding fallback/enrichment
3. **Open EV Data** for battery capacity matching

This keeps setup simple while still allowing fully online lookup of identity and battery data.

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

# Legal information

EV Guest uses third-party data sources and is **not affiliated with, endorsed by, or maintained by** Home Assistant, MotorAPI, NHTSA, or Open EV Data.

### Third-party services and datasets

- **MotorAPI** is used for Danish license plate lookups and VIN retrieval.
- **NHTSA vPIC** is used as a public VIN decoding fallback / enrichment source.
- **Open EV Data** is used for best-effort EV battery matching.

### Attribution

This project uses **Open EV Data** under its MIT License with Attribution Requirement. Attribution to **Open EV Data** is provided in this README.

### Data accuracy

EV Guest provides **best-effort** matching of brand, model, variant, and battery capacity.
Vehicle variants can differ across markets and model years. Always verify matched battery data if exact charging cost estimation is important.

### Privacy and API usage

License plates, VINs, and derived vehicle metadata may be sent to external services in order to retrieve vehicle information.
Users are responsible for their own MotorAPI key and for complying with the terms of any third-party services they use.

# Important notes

- EV Guest does **not** control a charger directly.
- EV Guest calculates the cheapest charging window and exposes the result as sensors.
- Currency selection changes only the output unit/currency label. It does **not** perform live FX conversion.
- The integration assumes linear AC charging based on entered charger power and battery capacity.
- If the online battery match is uncertain or unavailable, you should set battery capacity manually.

# Troubleshooting

### Car data not found

- Check that the license plate format is correct.
- Verify that your MotorAPI API key is valid.
- Some vehicles may not have a confident battery match in Open EV Data.

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
