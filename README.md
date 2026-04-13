# EV Guest

![EV Guest](https://raw.githubusercontent.com/Dinnsen/EV-Guest/main/docs/assets/logo.png)

[![GitHub Release][releases-shield]][releases]
[![GitHub All Releases][download-all-shield]][releases]
[![HACS][hacs-shield]][hacs]
[![BuyMeCoffee][buymecoffee-shield]][buymecoffee]

EV Guest for Home Assistant helps you find the cheapest charging window for guest EVs **without connecting the car to Home Assistant**.

The integration:
- looks up vehicle identity from the guest's license plate
- enriches vehicle data from the VIN when available
- matches the vehicle against Open EV Data to estimate battery capacity
- combines that with a supported electricity price sensor to calculate the cheapest charging plan
- can optionally control **one charger switch entity** directly
- can optionally observe a separate **charger status entity**

## Table of content
- [Installation](#installation)
- [Setup](#setup)
- [Configuration options](#configuration-options)
- [Usage](#usage)
- [Entities](#entities)
- [Service actions](#service-actions)
- [Supported electricity price sensors](#supported-electricity-price-sensors)
- [Vehicle lookup providers](#vehicle-lookup-providers)
- [Data update behavior](#data-update-behavior)
- [Legal information](#legal-information)
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
- **Country** (`Denmark`)
- **MotorAPI API key**
- **Optional Charger Switch Entity** (`switch.*`) for direct on/off charging control
- **Optional Charger Status Entity** (`binary_sensor.*`, `switch.*`, or `input_boolean.*`) so EV Guest can see whether the charger currently reports on/off

No user setup is needed for:
- **NHTSA vPIC**
- **Open EV Data**

# Configuration options

After setup, the options flow lets you change:
- Electricity Price Sensor
- Charge Costs Currency
- Clock format
- Charge Time format
- Country
- MotorAPI API key
- Charger Switch Entity (optional)
- Charger Status Entity (optional)

### Charger Switch Entity
Optional. Used only when **Enable Charger Control** is turned on inside EV Guest. If left blank, EV Guest still calculates plans but will not try to start or stop a charger.

### Charger Status Entity
Optional. Lets EV Guest read whether the charger currently appears to be on or off. This is useful when the switch used to control charging is different from the entity that reports charging state.

# Usage

1. Enter the plate in the license-plate text entity.
2. Press **Grab Car Data**.
3. Review the returned brand, model, variant, and battery estimate.
4. Set SoC, charger power, charge limit, and completion time.
5. Press **Calculate**.
6. Turn on **Enable Charger Control** only if you want EV Guest to control the configured charger switch.

If the online battery match is weak, set battery capacity manually and calculate again.

# Entities

## Input/helper entities
- License Plate
- SoC
- Battery Capacity
- Charger Power
- Charge Limit
- Charge Completion Time
- Use Charge Completion Time
- Enable Charger Control
- Continuous Charging Preferred
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

## Diagnostic entities
- Charge Now

### Charge Now
`binary_sensor.charge_now` is **on** whenever the current time is inside the planned charging window and **off** otherwise. It is intended for automations, dashboards and external charger logic.

# Supported electricity price sensors

EV Guest works with sensors exposing hourly prices in one of these layouts:
- `raw_today` / `raw_tomorrow` with `hour` + `price`
- `today` / `tomorrow` hourly arrays
- `forecast` with `hour` + `price`

The example sensor `sensor.energi_data_service` fits this pattern.

# Vehicle lookup providers

Currently supported:
- **Country:** Denmark
- **Default provider:** MotorAPI Denmark

The code is structured so additional countries and providers can be added later through pull requests without changing the stable entity model.

# Data update behavior

EV Guest listens for state changes on the selected electricity-price sensor and recalculates when needed. If a charger status entity is configured, EV Guest also listens for its state changes so the current charger status can be reflected in diagnostics and automations.

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

License plates, VINs, and derived vehicle metadata may be sent to external services while lookups are performed. Users are responsible for their own API keys and third-party service usage.

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
