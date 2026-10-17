# Changelog

All notable changes to EV Guest. The version is the one in `custom_components/ev_guest/manifest.json`.

## [0.10.0] - 2026-10-17

How far the guest car has come – without the car in Home Assistant.

### Added
- **Estimated SoC** (`sensor.ev_guest_estimated_soc`): the guest car's estimated charge level, from the plan without an energy meter and from the measured energy with one. Updated every minute while the car charges.
- **Behind plan** (`binary_sensor.ev_guest_behind_plan`), only with an energy meter: on when the charger has delivered clearly less than planned.
- The panel shows the measured charge level and warns when the car is behind its plan.

See [the release notes](docs/releases/v0.10.0.md).

## [0.9.0] - 2026-10-17

The EV Guest panel: everything in one place in the sidebar, with no custom cards.

### Added
- **EV Guest panel** in the sidebar and as an **app on the home screen** (`/ev_guest_app/app.html`). It follows your Home Assistant theme in light and dark mode and is in English and Danish.
  - A **price clock** with the next 24 hours of prices, the charging window, now and the deadline. The cost and the savings are in the middle.
  - The guest car on a **Danish license plate**, with lookup and a ring showing how sure the battery match is.
  - Drag the charge level **now** and the **target** on a battery. Charger power, **Ready by** and the type of plan are set with one tap each.
  - A **live preview** of the plan while you change something.
  - A **two-day price graph** with the charging periods.
  - **History** with totals, and a **bill** for the guest to copy or share. The bill uses the actual electricity price or your own price per kWh, plus your payment details.
- **15-minute prices** (and 30-minute). EV Guest reads the length of each price period, also from Nord Pool's `start`/`end`/`value` rows.
- **Charging efficiency** (default 90 %): energy from the grid, charging time and cost now include charging losses. Number entity `number.ev_guest_charging_efficiency`.
- **Savings** compared with charging right away: `sensor.ev_guest_savings`, with `charge_now_cost` and `average_price` attributes.
- **Energy needed** from the grid: `sensor.ev_guest_energy_needed`.
- **New guest** button and action `ev_guest.new_guest`. They clear the plate, the car and the plan; a finished plan is kept in the history.
- Optional **charger energy meter** (options). EV Guest measures the energy and cost actually used while the plan runs: `sensor.ev_guest_measured_energy` and `sensor.ev_guest_measured_cost`.
- Strict typing, completing Home Assistant's Platinum quality scale.

### Changed
- A plan can **start right away**, in the price period that is running now, instead of at the next whole hour.
- A continuous plan may also **end on a price change** (with the part period first), when that is cheaper.
- When there are prices up to the deadline but the car cannot finish in time, the status is now *No charging window* instead of *Waiting for prices*.
- `charging_schedule` and `raw_two_days` follow the sensor's price periods (e.g. 96 per day with 15-minute prices).
- The Open EV Data list is downloaded at most once a day.
- New icon and logo, correct for Home Assistant and HACS in light and dark mode.

### Removed
- The example dashboard (`docs/dashboard/ev_guest_dashboard.yaml`) and its three custom cards. The panel replaces it. Your existing dashboard keeps working, as all entities are unchanged.

### Fixed
- A reload (e.g. after an options change) right after a change could load the state from before the change.

### Upgrade notes
- With the default 90 % efficiency, plans take a little longer and cost a little more than in 0.8.0, because charging losses now count. Set **Charging efficiency** to 100 % for the old figures.
- Plans made with 0.8.0 are kept but not added to the history.

### Rollback
The config entry version is unchanged (7.1), so downgrading to 0.8.0 works. The new entities become unavailable, and the stored history is ignored by 0.8.0.

## [0.8.0] - 2026-10-06

Native Home Assistant entities, translated errors and states, reconfiguration, repairs, diagnostics and a test suite against real Home Assistant. See [the release notes](docs/releases/v0.8.0.md).

## [0.7.0]

EV Guest became a pure calculator: charger control was removed, and `binary_sensor.charge_now` follows the exact planned periods. See [the release notes](docs/releases/v0.7.0.md).

## [0.6.4] - 2026-04-13

Cheapest window without a completion time, and MotorAPI setup instructions. See [the release notes](docs/releases/v0.6.4.md).

## [0.6.0]

Charge Now binary sensor, country selection and an extensible lookup provider structure. See [the release notes](docs/releases/v0.6.0.md).
