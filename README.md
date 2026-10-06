# EV Guest

![EV Guest](https://raw.githubusercontent.com/Dinnsen/EV-Guest/main/docs/assets/logo.png)

[![GitHub Release][releases-shield]][releases]
[![Downloads][download-all-shield]][releases]
[![HACS][hacs-shield]][hacs]
[![Tests][tests-shield]][tests]
[![hassfest][hassfest-shield]][hassfest]
[![HACS validation][validate-shield]][validate]
[![BuyMeCoffee][buymecoffee-shield]][buymecoffee]

**Find the cheapest time to charge a guest's electric car – without connecting the car to Home Assistant.**

Enter the license plate, the car's current charge level and when it must be ready. EV Guest looks up the car, works out how much energy it needs and finds the cheapest charging window from your electricity prices. It then tells your automations exactly when to charge.

EV Guest is a calculator: it never switches a charger itself. Pair it with a simple automation or with [EV Smart Charging](https://github.com/jonasbkarlsson/ev_smart_charging) to do the charging.

## Contents

- [Features](#features)
- [Installation](#installation)
- [Setup](#setup)
- [Usage](#usage)
- [Entities](#entities)
- [Actions](#actions)
- [Dashboard](#dashboard)
- [Charging the car](#charging-the-car)
- [Live SoC](#live-soc)
- [How data is updated](#how-data-is-updated)
- [Supported price sensors](#supported-price-sensors)
- [Known limitations](#known-limitations)
- [Troubleshooting](#troubleshooting)
- [Removal](#removal)
- [Legal](#legal)

## Features

- **License plate lookup** (Denmark, via MotorAPI) with VIN decoding and battery capacity matched from Open EV Data. Optional – you can always enter the battery capacity yourself.
- **Cheapest charging plan** before a completion time, either as one continuous block or split across the cheapest hours.
- **`Charge now`** turns on exactly while the plan says charge, to the minute.
- **Plans that behave**: a plan is locked once it starts, survives restarts and follows new prices until it starts.
- **Native Home Assistant entities**: timestamps, durations, a status with translated states, a time picker for the completion time, and battery, power and energy device classes.
- **Fully translated** (English and Danish), with icons, repairs, diagnostics and reconfiguration.

### Use cases

- A guest arrives in the evening with 20 % battery and leaves at 07:00 – charge in the cheapest hours overnight.
- You rent out a parking spot with a charger and want to show the expected cost before charging.
- Your own cars are handled by EV Smart Charging, and you want the same smart charging for visitors whose cars are not in Home Assistant.

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open this repository in HACS.][my-hacs-badge]][my-hacs]

1. Open the link above, or add `https://github.com/Dinnsen/EV-Guest` as a custom repository in HACS (type **Integration**).
2. Install **EV Guest** and restart Home Assistant.

### Manual

1. Download `ev_guest.zip` from the [latest release][releases].
2. Unzip it into `config/custom_components/ev_guest`.
3. Restart Home Assistant.

## Setup

[![Open your Home Assistant instance and start setting up EV Guest.][my-config-badge]][my-config]

Add **EV Guest** under **Settings → Devices & services → Add integration**.

| Setting | Description |
| --- | --- |
| Name | Device name, for example *EV Guest*. Each EV Guest needs its own name. |
| Electricity price sensor | A sensor with hourly prices for today and tomorrow (see [supported price sensors](#supported-price-sensors)). It is checked during setup. |
| Country | Country used for license plate lookup. Currently Denmark. |
| MotorAPI API key | Optional. Needed only for license plate lookup. Get a free key at [motorapi.dk](https://www.motorapi.dk/): enter your email under *Få adgang nu* and the key arrives by email. |
| Currency | Currency of the electricity prices, used for the charge cost. Defaults to your Home Assistant currency. |

After setup:

- **Reconfigure** changes the price sensor, country or MotorAPI key.
- **Configure** (options) changes the currency. Changes apply immediately, no restart needed.
- If the MotorAPI key stops working, Home Assistant asks you for a new one.

## Usage

1. Enter the guest's **license plate** and press **Grab car data**. Check the brand, model and battery capacity. If the match is wrong, set the battery capacity yourself.
2. Set the car's current **SoC**, the **charge limit**, the **charger power** and the **charge completion time**.
3. Press **Calculate**. The status changes to *Planned* and the start, end, duration and cost appear.
4. Let an automation or EV Smart Charging follow the plan (see [Charging the car](#charging-the-car)).

Inputs and the current plan are stored and survive a restart. Press **Calculate** again for the next guest.

## Entities

| Entity | Type | Description |
| --- | --- | --- |
| License plate | Text | The guest car's plate. |
| SoC (State of Charge) | Number (%) | The car's charge level now. |
| Charge limit | Number (%) | The charge level to reach. |
| Battery capacity | Number (kWh) | Filled in by the lookup, or set it yourself. |
| Charger power | Number (kW) | The charging power of your charger. |
| Charge completion time | Time | When the car must be charged. |
| Use charge completion time | Switch | Off: plan freely within the next 48 hours of prices. |
| Continuous charging preferred | Switch | On: one block. Off: the cheapest hours, split if cheaper. |
| Grab car data | Button | Look up the car from the plate. |
| Calculate | Button | Make a new plan. |
| Charge now | Binary sensor | On exactly while the plan says charge. |
| Status | Sensor (enum) | *Ready*, *Planned*, *Charging*, *Completed*, or why the last calculation failed. |
| Charge start time / Charge end time | Sensor (timestamp) | Start of the first and end of the last charging period. |
| Charge time | Sensor (duration) | Total charging time. |
| Charge costs | Sensor (monetary) | Expected cost of the plan. |
| Charging speed | Sensor (%/h) | Charge level gained per hour, e.g. for EV Smart Charging. |
| Car brand / model / variant / battery capacity | Sensor (diagnostic) | Result of the lookup. |

### Status attributes

| Attribute | Description |
| --- | --- |
| `charging_segments` | The exact planned periods as `start`/`end`. |
| `charging_schedule` | The plan per hour (1 = charging), aligned with `raw_two_days`, for graphs. |
| `raw_two_days` | The prices used, for graphs. |
| `plan_mode` | `continuous` or `split`. |
| `plan_locked` | `true` once the plan has started. |
| `last_calculation`, `last_lookup`, `vin`, `model_year`, `fuel_type`, `match_score` | Details of the last calculation and lookup. |

## Actions

| Action | Description |
| --- | --- |
| `ev_guest.grab_car_data` | Look up the car from the license plate. |
| `ev_guest.calculate` | Make a new charging plan. |

Both take an optional `config_entry_id`; it can be left out when you have only one EV Guest. When an action fails, Home Assistant shows why, for example *Enter a license plate first*.

```yaml
action: ev_guest.calculate
```

## Dashboard

<!-- SCREENSHOT -->

[`docs/dashboard/ev_guest_dashboard.yaml`](docs/dashboard/ev_guest_dashboard.yaml) is a ready-made dashboard: license plate lookup, car data, inputs, the charging plan and a two-day price graph with the planned charging hours.

**It needs three custom cards from HACS** (HACS → search → Download, then reload the browser):

| Card | Used for |
| --- | --- |
| [Bubble Card](https://github.com/Clooos/Bubble-Card) | Headers, buttons and sliders |
| [ApexCharts Card](https://github.com/RomRider/apexcharts-card) | Price graph with the charging plan |
| [Vertical Stack In Card](https://github.com/ofekashery/vertical-stack-in-card) | Groups the graph with its title |

**To add it:**

1. Go to **Settings → Dashboards → Add dashboard → New dashboard from scratch**, and open the new dashboard.
2. Choose **⋮ → Edit dashboard → ⋮ → Raw configuration editor**.
3. Paste the contents of `ev_guest_dashboard.yaml` and save.

To add it as a tab in an existing dashboard instead, paste only the view (everything under `views:`) into that dashboard's raw configuration.

The entity IDs assume your EV Guest is named *EV Guest*. If you chose another name, replace `ev_guest_` with your own prefix. The graph reads the `raw_two_days` and `charging_schedule` attributes of the status sensor, so it works with any supported price sensor.

## Charging the car

### With an automation

```yaml
automation:
  - alias: Guest charging follows EV Guest
    triggers:
      - trigger: state
        entity_id: binary_sensor.ev_guest_charge_now
    actions:
      - action: >-
          switch.turn_{{ 'on' if trigger.to_state.state == 'on' else 'off' }}
        target:
          entity_id: switch.my_charger
```

### With EV Smart Charging

[EV Smart Charging](https://github.com/jonasbkarlsson/ev_smart_charging) accepts any entity with a value from 0 to 100 as SoC, so an EV Smart Charging entry for guest cars can read EV Guest directly:

- **EV SOC entity**: `number.ev_guest_soc_state_of_charge`
- **EV target SOC entity**: `number.ev_guest_charge_limit`
- **Charger control entity**: your charger's switch (a guest car is not in Home Assistant)

Charging speed and completion time are settings inside EV Smart Charging. Copy them with an automation: `sensor.ev_guest_charging_speed` (%/h) → `number.ev_smart_charging_charging_speed`, and the completion time (whole hours) → `select.ev_smart_charging_charge_completion_time`. EV Smart Charging then makes its own plan; EV Guest's plan is a preview.

## Live SoC

EV Guest only knows the SoC you enter; it never sees the car's charge level while charging.

- **EV Guest locks a plan once it starts.** New prices can move a plan that has not started (for example when tomorrow's prices arrive), but never a running or finished plan – otherwise a fixed start SoC would make the plan slide forward and charge twice. Press **Calculate** to plan again.
- **EV Smart Charging** does not rebuild its schedule while the SoC stays the same after charging has started, so a fixed start SoC works there too. If Home Assistant restarts while charging, EV Smart Charging plans again from the start SoC; the car's own charge limit is the safety net.

## How data is updated

EV Guest does not poll. It updates when:

- you change an input or press a button,
- the price sensor changes – after your first **Calculate**, and only until the plan starts,
- a planned charging period starts or ends (to the second).

The license plate lookup only contacts MotorAPI, NHTSA and Open EV Data when you press **Grab car data**.

## Supported price sensors

Any sensor exposing hourly prices in one of these layouts:

- `raw_today` / `raw_tomorrow` (or `forecast`) lists with `hour` and `price` – e.g. **Energi Data Service**, **Nord Pool** (HACS)
- `today` / `tomorrow` lists of hourly prices from midnight

## Known limitations

- Prices are used per hour. Sensors with 15-minute prices are not supported yet.
- License plate lookup supports Denmark only.
- The battery match from Open EV Data is a best guess; check it, especially for rare variants.
- Charging is assumed to run at the set charger power the whole time; real cars slow down near full.
- EV Guest does not see the car's live charge level (see [Live SoC](#live-soc)).

## Troubleshooting

| Problem | What to do |
| --- | --- |
| *The sensor has no hourly prices EV Guest can read* during setup | Choose the price sensor itself, not a template showing only the current price. Check that it has `raw_today` or `today` attributes. |
| Status *Waiting for prices* | Not enough prices are known before the completion time yet. EV Guest calculates again when new prices arrive (usually after 13:00). |
| Status *No charging window* | The car needs more time than there is before the completion time. Raise the charger power, lower the charge limit or move the completion time. |
| A repair says the price sensor is missing | Use **Reconfigure** on the EV Guest integration to choose another sensor. |
| *Grab car data* says a MotorAPI key is needed | Add a key under **Reconfigure**, or set the battery capacity yourself. |
| Car sensors are unavailable | The last lookup could not reach MotorAPI. Try again later. |

For bug reports, attach the diagnostics (**Settings → Devices & services → EV Guest → ⋮ → Download diagnostics**). License plate, VIN and API key are removed automatically.

## Removal

1. Go to **Settings → Devices & services → EV Guest**, open the menu and choose **Delete**. Stored inputs and plans are removed too.
2. Optionally remove EV Guest in HACS and restart Home Assistant.

## Legal

EV Guest is not affiliated with, endorsed by, or maintained by Home Assistant, MotorAPI, NHTSA or Open EV Data. License plates, VINs and derived vehicle data are sent to MotorAPI, NHTSA and Open EV Data when you press **Grab car data**. You are responsible for your own API key and use of these services.

[releases-shield]: https://img.shields.io/github/v/release/Dinnsen/EV-Guest?style=for-the-badge
[download-all-shield]: https://img.shields.io/github/downloads/Dinnsen/EV-Guest/total?style=for-the-badge
[hacs-shield]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge
[tests-shield]: https://img.shields.io/github/actions/workflow/status/Dinnsen/EV-Guest/tests.yml?branch=main&label=tests&style=for-the-badge
[hassfest-shield]: https://img.shields.io/github/actions/workflow/status/Dinnsen/EV-Guest/hassfest.yml?branch=main&label=hassfest&style=for-the-badge
[validate-shield]: https://img.shields.io/github/actions/workflow/status/Dinnsen/EV-Guest/validate.yml?branch=main&label=HACS&style=for-the-badge
[buymecoffee-shield]: https://img.shields.io/badge/Buy%20Me%20a%20Coffee-support-ffdd00?style=for-the-badge
[releases]: https://github.com/Dinnsen/EV-Guest/releases
[hacs]: https://github.com/hacs/integration
[tests]: https://github.com/Dinnsen/EV-Guest/actions/workflows/tests.yml
[hassfest]: https://github.com/Dinnsen/EV-Guest/actions/workflows/hassfest.yml
[validate]: https://github.com/Dinnsen/EV-Guest/actions/workflows/validate.yml
[buymecoffee]: https://buymeacoffee.com/dinnsen
[my-hacs-badge]: https://my.home-assistant.io/badges/hacs_repository.svg
[my-hacs]: https://my.home-assistant.io/redirect/hacs_repository/?owner=Dinnsen&repository=EV-Guest&category=integration
[my-config-badge]: https://my.home-assistant.io/badges/config_flow_start.svg
[my-config]: https://my.home-assistant.io/redirect/config_flow_start/?domain=ev_guest
