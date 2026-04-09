# EV Guest test notes

These files focus on the lowest-friction unit-style tests first:
- API helper normalization and candidate matching
- coordinator calculation logic
- diagnostics redaction

Recommended next files to add in the repo itself:
- `tests/test_config_flow.py`
- `tests/test_reauth_flow.py`
- `tests/test_init.py`
- `tests/test_sensor.py`

Those are better added once the repo is wired to the Home Assistant pytest test harness.
