# EV Guest

EV Guest helps Home Assistant calculate the cheapest charging window for guest EVs without pairing the car directly to Home Assistant. The current upstream release is `0.4.0`, with UI setup, MotorAPI-backed Danish plate lookup, price-sensor planning, and basic charger control already present.

This `0.5.0` release pack builds on that structure and keeps migration in place from older config entries by preserving the existing charger switch setting while adding new defaults for charger profile, language, and country. The existing integration already stores config via config entries and includes migration logic, which is why extending the entry format is the safest way to stay HACS-update friendly.

## English

### What is new in this pack

- Language selection in configuration: `English` and `Dansk`
- Country selection in configuration: `Denmark` for now
- Future-ready country/provider structure so contributors can add more countries through pull requests
- Tighter charger profile mapping for:
  - Generic switch
  - OK charger
  - Easee
  - Zaptec GO
  - Tesla Wall Connector
  - Home Assistant EV Smart Charging
  - Dummy Test Charger
- Expanded charger diagnostics and control actions
- Updated logo assets

### Country and provider model

The current upstream package is effectively Denmark-first because vehicle lookup is done with MotorAPI and then enriched with VIN and Open EV Data. This pack formalizes that by introducing an explicit `country` setting with `dk` as the only built-in option for now, and a provider registry layer behind it so more countries can be added later without rewriting the rest of the integration.

### Charger profiles

EV Guest already supports charger planning and generic charger control through the configured charger entity and optional service overrides. This pack keeps that design and makes the profiles clearer and safer in the config flow. The existing coordinator already plans callbacks, reconciles expected state, and calls either service overrides or `<domain>.turn_on` / `<domain>.turn_off` on the selected charger entity.

Recommended mapping in this pack:

- **Generic switch**: requires a `switch.*` charger entity
- **OK / Easee / Zaptec GO / Tesla Wall Connector**: requires a `switch.*` charger entity, with status entity optional
- **HA EV Smart Charging**: requires either a charger entity or both start/stop service overrides
- **Dummy Test Charger**: no real charger required; use it to validate EV Guest control logic

### Setup notes

For Denmark, use a supported hourly price sensor such as one exposing `raw_today`, `raw_tomorrow`, `today`, `tomorrow`, or `forecast`, which is how the upstream integration already expects price data.

### Pull requests for new countries

To add a new country later, contributors only need to:

1. add a new country constant and selector option
2. add a provider mapping in the provider registry
3. implement provider validation and plate lookup in `api.py`
4. add translations and README notes

## Dansk

### Hvad er nyt i denne pakke

- Sprogvalg i opsætning: `English` og `Dansk`
- Land i opsætning: `Danmark` indtil videre
- Fremtidssikret struktur til nummerplade-API pr. land, så andre kan lave pull requests med flere lande
- Strammere ladeprofiler til:
  - Generic switch
  - OK-lader
  - Easee
  - Zaptec GO
  - Tesla Wall Connector
  - Home Assistant EV Smart Charging
  - Dummy Test Charger
- Udvidet ladediagnostik og styringsknapper
- Opdaterede logo-filer

### Land og provider

Den nuværende upstream-integration er i praksis bygget til Danmark, fordi opslag starter i MotorAPI og derefter beriger data med VIN-opslag og Open EV Data. Denne pakke gør det eksplicit med et `country`-valg og et lille provider-lag, så flere lande kan tilføjes senere uden at omskrive hele integrationen.

### Ladeprofiler

Den eksisterende coordinator i repoet laver allerede ladeplan, planlagte callbacks og generisk start/stop via valgt entity eller service override. Denne pakke bygger videre på den model, men gør valg og validering tydeligere i config flow.

Anbefalet mapping i denne pakke:

- **Generic switch**: kræver en `switch.*`-entity
- **OK / Easee / Zaptec GO / Tesla Wall Connector**: kræver en `switch.*`-entity, status-entity er valgfri
- **HA EV Smart Charging**: kræver enten en lader-entity eller både start- og stop-service override
- **Dummy Test Charger**: kræver ingen rigtig lader og bruges til test af EV Guest-styringen

### Vigtige filer i pakken

- `custom_components/ev_guest/__init__.py`
- `custom_components/ev_guest/api.py`
- `custom_components/ev_guest/config_flow.py`
- `custom_components/ev_guest/coordinator.py`
- `custom_components/ev_guest/const.py`
- `custom_components/ev_guest/strings.json`
- `custom_components/ev_guest/translations/da.json`
- `custom_components/ev_guest/translations/en.json`
- `custom_components/ev_guest/brand/logo.svg`
- `custom_components/ev_guest/brand/icon.svg`

## Important note

This pack is designed to be migration-friendly from the current `v0.4.0` config-entry structure. It is syntax-checked locally, but the vendor profiles still rely on the Home Assistant entities and services exposed by each installed charger integration, so final runtime verification should be done in Home Assistant after upload. The current upstream package already documents HACS/manual install, config-entry setup, entities, and supported price-sensor layouts, which this pack intentionally extends rather than replacing.


## Repository structure in this complete pack

This download includes the full repository layout:

- `.github/workflows`
- `custom_components/ev_guest`
- `docs/dashboard`
- `docs/screenshots`
- `tests`
- root project files such as `.gitignore`, `LICENSE`, `README.md`, and `hacs.json`

## Migration note

The package keeps config-entry migration in `custom_components/ev_guest/__init__.py` and extends the existing configuration keys rather than replacing them. That is the part intended to let existing `v0.4.0` users update in HACS and keep their current entries.
