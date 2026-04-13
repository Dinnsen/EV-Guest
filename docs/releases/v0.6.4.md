## EV Guest v0.6.4

This release fixes charging-plan selection when **Use Charge Completion Time** is turned off and updates the setup documentation.

### Fixed
- Fixed cheapest-window calculation when **Use Charge Completion Time** is disabled
- Fixed charging plans selecting hours outside the 2-day dashboard horizon
- Fixed `charging_schedule` so the planned charging window is shown correctly in dashboards that use the built-in `raw_two_days` and `charging_schedule` attributes

### Changed
- Updated setup documentation with step-by-step instructions for creating a MotorAPI API key
- Bumped integration version to `0.6.4`

### Notes
When **Use Charge Completion Time** is off, EV Guest now chooses the cheapest charging window from the same visible 2-day planning horizon that is exposed to the dashboard graph.
