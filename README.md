# EV Guest

![EV Guest](https://raw.githubusercontent.com/Dinnsen/EV-Guest/main/docs/assets/logo.png)

[![GitHub Release][releases-shield]][releases]
[![GitHub All Releases][download-all-shield]][releases]
[![HACS][hacs-shield]][hacs]
[![BuyMeCoffee][buymecoffee-shield]][buymecoffee]

EV Guest for Home Assistant helps you find the cheapest charging window for guest EVs without connecting the car to Home Assistant.

EV Guest is a calculator. It does not start or stop charging itself; it tells you (and your automations) when to charge.

The integration:
- looks up vehicle identity from the guest's license plate (optional, needs a MotorAPI key)
- enriches vehicle data from the VIN when available
- matches the vehicle against Open EV Data to estimate battery capacity
- combines that with a supported electricity price sensor to calculate the cheapest charging plan
- exposes the plan through `binary_sensor.charge_now` so any charger can follow it
- can feed EV Smart Charging with SoC, target SoC and charging speed for a guest car

## Table of content
- [Installation](#installation)
- [Setup](#setup)
- [Configuration options](#configuration-options)
- [Usage](#usage)
- [Entities](#entities)
- [Service actions](#service-actions)
- [Charging the car](#charging-the-car)
- [Live SoC](#live-soc)
- [Supported electricity price sensors](#supported-electricity-price-sensors)
- [Vehicle lookup providers](#vehicle-lookup-providers)
- [Data update behavior](#data-update-behavior)
- [Legal information](#legal-information)
- [Removal](#removal)

# Installation

### Option 1 - HACS
- Ensure HACS is installed.
- Add this repository as a custom repository in HACS with category Integration.
- Install EV Guest.
- Restart Home Assistant.

### Option 2 - Manual
- Download the latest release.
- Copy `custom_components/ev_guest` into your Home Assistant `custom_components` folder.
- Restart Home Assistant.

# Setup

Add EV Guest from Settings → Devices & Services.

License plate lookup is optional. Without a MotorAPI key EV Guest still calculates plans; you just enter battery capacity manually.

To use license plate lookup, create a MotorAPI API key:
1. Go to https://www.motorapi.dk/
2. Enter your email address under **Få adgang nu**
3. Submit the form and wait for the email with your API key
4. Paste that API key into EV Guest during setup

During setup, EV Guest asks for:
- Name
- Electricity Price Sensor
- Charge Costs Currency (`DKK`, `EUR`, `USD`)
- Clock format (`24h` or `12h`)
- Charge Time format (`minutes` or `hours_minutes`)
- Country (`Denmark`)
- MotorAPI API key (optional)

No user setup is needed for:
- NHTSA vPIC
- Open EV Data

# Configuration options

After setup, the options flow lets you change:
- Electricity Price Sensor
- Charge Costs Currency
- Clock format
- Charge Time format
- Country
- MotorAPI API key (leave empty to keep the current one)

# Usage

1. Enter the plate in the license-plate text entity.
2. Press Grab Car Data.
3. Review the returned brand, model, variant, and battery estimate.
4. Set SoC, charger power, charge limit, and completion time.
5. Press Calculate.
6. Let an automation or EV Smart Charging follow the plan (see [Charging the car](#charging-the-car)).

If the online battery match is weak, set battery capacity manually and calculate again.

Inputs and the current plan are saved and survive a Home Assistant restart.

# Entities

## Input/helper entities
- License Plate
- SoC
- Battery Capacity
- Charger Power
- Charge Limit
- Charge Completion Time
- Use Charge Completion Time
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
- Charge Now

### Charge Now
`binary_sensor.charge_now` is on exactly while the current time is inside a planned charging segment and off otherwise, to the minute (a plan ending at 03:20 turns off at 03:20). It is intended for automations, dashboards and external charger logic.

### Status attributes
- `charging_segments`: the exact planned intervals (`start`/`end`)
- `charging_schedule`: the same plan per hour, for graphs together with `raw_two_days`
- `plan_locked`: `true` once the plan has started (see [Live SoC](#live-soc))
- `plan_mode`: `continuous` or `split`

### Split charging
With **Continuous Charging Preferred** off, EV Guest picks the cheapest hours anywhere before the completion time. Full hours go to the cheapest hours and a remaining part-hour goes to the next-cheapest hour. A part-hour next to another charging hour is placed so the two join up.

# Charging the car

EV Guest does not control a charger. Use one of these:

### Simple automation
Turn the charger on when `binary_sensor.ev_guest_charge_now` turns on and off when it turns off.

### EV Smart Charging
[EV Smart Charging](https://github.com/jonasbkarlsson/ev_smart_charging) accepts any entity with a value from 0 to 100 as SoC, so a dedicated EV Smart Charging instance for guest cars can use EV Guest directly:
- **EV SOC entity**: `number.ev_guest_soc_state_of_charge`
- **EV target SOC entity**: `number.ev_guest_charge_limit`
- **Charger control entity**: the charger's own switch (a guest car is not in Home Assistant)

Charging speed and completion time live inside EV Smart Charging. Copy them with an automation:
- `sensor.ev_guest_charging_speed` (%/h) → `number.ev_smart_charging_charging_speed`
- the completion time (whole hours) → `select.ev_smart_charging_charge_completion_time`

EV Smart Charging then makes its own plan from the same inputs. EV Guest's plan is a preview in that setup.

# Live SoC

EV Guest only knows the SoC you enter. It never sees the car's live SoC while it charges.

- **EV Guest's own plan is locked once it starts.** Price updates can move a plan that has not started yet (for example when tomorrow's prices arrive), but never a plan that is running or finished. Otherwise a static start SoC would make the plan slide forward and charge the same energy twice. Press **Calculate** to make a new plan for the next guest.
- **EV Smart Charging** does not rebuild its schedule while the SoC stays unchanged after charging has started, so a static start SoC works there too. One caveat: if Home Assistant restarts in the middle of charging, EV Smart Charging plans again from the start SoC. The car's own charge limit is the safety net.

# Supported electricity price sensors

EV Guest works with sensors exposing hourly prices in one of these layouts:
- `raw_today` / `raw_tomorrow` with `hour` + `price`
- `today` / `tomorrow` hourly arrays
- `forecast` with `hour` + `price`

The example sensor `sensor.energi_data_service` fits this pattern.

# Vehicle lookup providers

Currently supported:
- Country: Denmark
- Default provider: MotorAPI Denmark

The code is structured so additional countries and providers can be added later through pull requests without changing the stable entity model.

# Data update behavior

After you press **Calculate**, EV Guest listens for state changes on the selected electricity-price sensor and recalculates until the plan starts. Prices are expected per hour.

# Legal information

EV Guest is not affiliated with, endorsed by, or maintained by Home Assistant, MotorAPI, NHTSA, or Open EV Data.

Third-party sources used:
- MotorAPI for Danish license plate and VIN lookup
- NHTSA vPIC for VIN decoding fallback
- Open EV Data for battery matching

License plates, VINs, and derived vehicle metadata may be sent to external services while lookups are performed. Users are responsible for their own API keys and third-party service usage.

# Removal

To remove EV Guest:
- Go to Settings → Devices & Services
- Open EV Guest
- Choose Delete
- Restart Home Assistant if you installed it manually and want to remove the files from `custom_components`

[releases-shield]: https://img.shields.io/github/v/release/Dinnsen/EV-Guest?style=for-the-badge
[download-all-shield]: https://img.shields.io/github/downloads/Dinnsen/EV-Guest/total?style=for-the-badge
[hacs-shield]: https://img.shields.io/badge/HACS-Custom-blue.svg?style=for-the-badge
[buymecoffee-shield]: https://img.shields.io/badge/Buy%20Me%20a%20Coffee-support-ffdd00?style=for-the-badge
[releases]: https://github.com/Dinnsen/EV-Guest/releases
[hacs]: https://github.com/hacs/integration
[buymecoffee]: https://buymeacoffee.com/dinnsen
