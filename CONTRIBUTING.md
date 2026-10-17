# Contributing to EV Guest

Thanks for helping! This page shows how to ask for something and where things live in the code.

## Ask for something

Open an [issue](https://github.com/Dinnsen/EV-Guest/issues/new/choose) and pick a template:

- **Bug report** – something does not work as expected.
- **Feature request** – an idea for EV Guest.
- **New country / license plate lookup** – EV Guest in your country. It asks for the lookup service, an example answer from it and what license plates look like.
- **Translation** – EV Guest in your language, or a fix to a translation.

Please never post real license plates, API keys or other personal data.

## Development

You need Python 3.14.

```bash
pip install -r requirements_test.txt
pytest --cov                       # tests, at least 95 % coverage
mypy                               # strict typing
ruff check . && ruff format .      # lint and format
```

GitHub Actions runs the same checks, plus hassfest and HACS validation, on every pull request.

The tests run against a real Home Assistant (`pytest-homeassistant-custom-component`). External services are never called: mock them with `aioclient_mock`, as `tests/test_api_http.py` does.

## Where things are

| File | What it does |
| --- | --- |
| `custom_components/ev_guest/coordinator.py` | State, inputs, the guest session, history and the energy meter |
| `planner.py` | The cheapest charging plan (pure Python, no Home Assistant) |
| `progress.py` | The estimated charge level while charging (pure Python) |
| `prices.py` | Reading price sensors (Energi Data Service, Nord Pool, …) |
| `api.py` | License plate lookup (MotorAPI), NHTSA VIN decoding and Open EV Data battery sizes |
| `sensor.py`, `binary_sensor.py`, `number.py`, … | Entities |
| `websocket.py`, `panel.py`, `frontend/ev-guest-panel.js` | The sidebar panel |
| `strings.json`, `translations/*.json` | Entity names, settings and errors |
| `blueprints/automation/ev_guest/` | The blueprint that lets a charger follow EV Guest |

## Add a language

A language has two parts: Home Assistant's texts and the panel's texts.

1. **Home Assistant texts.** Copy `custom_components/ev_guest/translations/en.json` to `translations/<code>.json`, using Home Assistant's language code (e.g. `sv`, `nb`, `de`). Translate the values, never the keys. Keep placeholders such as `{detail}` and `{entity_id}` as they are.
2. **Panel texts.** In `custom_components/ev_guest/frontend/ev-guest-panel.js`, the `TEXT` object at the top has a block per language (`da`, `en`). Add a block for your language with the same keys as `en`. A key you leave out falls back to English, so a partial translation still works. Keep placeholders such as `{time}` and `{pct}`.
3. **Dates and numbers.** The panel formats them with the Home Assistant user's locale. If your language needs a specific locale (as Danish uses `da-DK`), add it to `_locale` in the panel.
4. **README (optional).** A translated README is welcome as `README.<code>.md`; link it from the top of `README.md`.

Check the result by switching your Home Assistant user profile to the language: the entities, settings and panel should all change.

## Add a country (license plate lookup)

Planning, prices and charger control already work in any country. A country adds the license plate lookup, and the plate drawn in the panel.

1. **Country.** Add it to `COUNTRIES` in `const.py`; the setup offers it in the country list.
2. **Lookup provider.** In `api.py`:
   - add the provider to `PLATE_PROVIDER_REGISTRY` under the country, with a `label`, how it authenticates (`auth`) and a link to its documentation (`docs`);
   - write `async_lookup_vehicle_<provider>()` that returns a `VehicleLookupResult` (plate, VIN, brand, model, variant, model year, fuel type). Raise `EVGuestAuthError` for a bad key and `EVGuestLookupError` with a short reason (`vehicle_not_found`, `cannot_connect`, `timeout`, …) for everything else;
   - if the provider needs a key, write a harmless request that checks it;
   - call your functions from `async_validate_plate_provider_credentials()` and `async_lookup_vehicle()`, next to MotorAPI.
   The battery size is found from brand, model and variant in Open EV Data, so it works for every country.
3. **The plate in the panel.** The panel draws a Danish plate today (the `.plate` element with the `DK` EU band in `ev-guest-panel.js`). A new country needs its own look: the country code in the band, colours and letter format. Describe it in the issue if you are not making the pull request yourself.
4. **Setup texts.** The setup and settings describe MotorAPI; make them describe your provider too, in `strings.json` and every `translations/*.json`.
5. **Tests.** Mock the provider's API in `tests/test_api_http.py` – a found car, an unknown plate, a bad key and a timeout – and add the country to `tests/test_config_flow.py`.
6. **Docs.** Add the country to *Setup* and *Known limitations* in the READMEs.

## Pull requests

- Keep a pull request to one thing, with tests for what it changes.
- Update `CHANGELOG.md` under a new version, and the READMEs when behaviour changes.
- Don't change entity IDs or unique IDs: dashboards and automations depend on them.
- Write user-facing texts in plain words, in English and Danish (or leave a note, and a maintainer will add the Danish).
