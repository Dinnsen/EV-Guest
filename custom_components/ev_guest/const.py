"""Constants for EV Guest."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "ev_guest"
DEFAULT_NAME = "EV Guest"
PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.TEXT,
    Platform.TIME,
]
USER_AGENT = "EVGuestHomeAssistant/0.8.0 (+https://github.com/Dinnsen/EV-Guest)"

MOTORAPI_BASE_URL = "https://v1.motorapi.dk"
NHTSA_DECODE_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValuesExtended/{vin}?format=json"
OPEN_EV_DATA_URL = "https://raw.githubusercontent.com/KilowattApp/open-ev-data/main/data/ev-data.json"
OPEN_EV_DATA_FALLBACK_URL = "https://raw.githubusercontent.com/KilowattApp/open-ev-data/master/data/ev-data.json"

CONF_PRICE_ENTITY = "price_entity"
CONF_CURRENCY = "currency"
CONF_MOTORAPI_KEY = "motorapi_api_key"
CONF_COUNTRY = "country"
CONF_PLATE_PROVIDER = "plate_provider"

# Settings that belong to the connection (changed via reconfigure) as opposed
# to preferences (changed via options).
CONNECTION_KEYS = (CONF_PRICE_ENTITY, CONF_COUNTRY, CONF_MOTORAPI_KEY)

COUNTRY_DENMARK = "Denmark"
DEFAULT_COUNTRY = COUNTRY_DENMARK
DEFAULT_PLATE_PROVIDER = "motorapi_dk"
DEFAULT_PRICE_ENTITY = "sensor.energi_data_service"
DEFAULT_CURRENCY = "DKK"

CURRENCIES = ["DKK", "EUR", "USD", "SEK", "NOK"]
COUNTRIES = [COUNTRY_DENMARK]

INPUT_LICENSE_PLATE = "license_plate"
INPUT_SOC = "soc"
INPUT_BATTERY_CAPACITY = "battery_capacity"
INPUT_CHARGER_POWER = "charger_power"
INPUT_CHARGE_LIMIT = "charge_limit"
INPUT_CHARGE_COMPLETION_TIME = "charge_completion_time"
INPUT_USE_COMPLETION_TIME = "use_completion_time"
INPUT_CONTINUOUS_CHARGING_PREFERRED = "continuous_charging_preferred"

DEFAULT_COMPLETION_TIME = "07:00"

RESULT_CHARGING_SPEED = "charging_speed"
RESULT_CHARGE_START_TIME = "charge_start_time"
RESULT_CHARGE_END_TIME = "charge_end_time"
RESULT_CHARGE_TIME = "charge_time"
RESULT_CHARGE_COSTS = "charge_costs"
RESULT_CAR_BRAND = "car_brand"
RESULT_CAR_MODEL = "car_model"
RESULT_CAR_VARIANT = "car_variant"
RESULT_CAR_BATTERY_CAPACITY = "car_battery_capacity"
RESULT_STATUS = "status"

DIAGNOSTIC_CHARGE_NOW = "charge_now"

# Status sensor (enum): the state of the current plan, or why the last
# calculation failed. Lookup errors are only raised as action errors.
STATUS_READY = "ready"
STATUS_PLANNED = "planned"
STATUS_CHARGING = "charging"
STATUS_COMPLETED = "completed"
ERROR_LICENSE_PLATE_REQUIRED = "license_plate_required"
ERROR_MOTORAPI_KEY_MISSING = "motorapi_key_missing"
ERROR_INVALID_API_KEY = "invalid_api_key"
ERROR_VEHICLE_NOT_FOUND = "vehicle_not_found"
ERROR_LOOKUP_FAILED = "lookup_failed"
ERROR_INVALID_INPUT = "invalid_input"
ERROR_LIMIT_NOT_ABOVE_SOC = "limit_not_above_soc"
ERROR_NO_PRICE_DATA = "no_price_data"
ERROR_NOT_ENOUGH_PRICES = "not_enough_prices"
ERROR_NO_WINDOW = "no_window"
STATUS_OPTIONS = [
    STATUS_READY,
    STATUS_PLANNED,
    STATUS_CHARGING,
    STATUS_COMPLETED,
    ERROR_INVALID_INPUT,
    ERROR_LIMIT_NOT_ABOVE_SOC,
    ERROR_NO_PRICE_DATA,
    ERROR_NOT_ENOUGH_PRICES,
    ERROR_NO_WINDOW,
]

ATTR_LAST_LOOKUP = "last_lookup"
ATTR_LAST_CALCULATION = "last_calculation"
ATTR_LAST_SOURCE = "last_source"
ATTR_VIN = "vin"
ATTR_MODEL_YEAR = "model_year"
ATTR_FUEL_TYPE = "fuel_type"
ATTR_MATCH_SCORE = "match_score"
ATTR_CHARGING_SCHEDULE = "charging_schedule"
ATTR_RAW_TWO_DAYS = "raw_two_days"
ATTR_PLAN_MODE = "plan_mode"
ATTR_CHARGING_SEGMENTS = "charging_segments"
ATTR_PLAN_LOCKED = "plan_locked"
ATTR_ERROR_DETAIL = "error_detail"
ATTR_COUNTRY = "country"
ATTR_PLATE_PROVIDER = "plate_provider"

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.{{entry_id}}"

# Entities removed in later versions, cleaned from the entity registry on setup
# as (platform, key) pairs.
LEGACY_ENTITIES = (
    ("switch", "enable_charger_control"),  # charger control, removed in 0.7.0
    ("text", INPUT_CHARGE_COMPLETION_TIME),  # replaced by a time entity in 0.8.0
)

DATASET_CACHE_KEY = f"{DOMAIN}_open_ev_data_cache"

SERVICE_GRAB_CAR_DATA = "grab_car_data"
SERVICE_CALCULATE = "calculate"
ATTR_CONFIG_ENTRY_ID = "config_entry_id"

ISSUE_PRICE_ENTITY_MISSING = "price_entity_missing"

REDACT_KEYS = {CONF_MOTORAPI_KEY, ATTR_VIN, INPUT_LICENSE_PLATE}
