"""Constants for EV Guest."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "ev_guest"
DEFAULT_NAME = "EV Guest"
PLATFORMS = ["sensor", "button", "number", "text", "switch", "binary_sensor"]
DEFAULT_SCAN_INTERVAL = timedelta(minutes=30)
USER_AGENT = "EVGuestHomeAssistant/0.7.0 (+https://github.com/Dinnsen/EV-Guest)"

MOTORAPI_BASE_URL = "https://v1.motorapi.dk"
NHTSA_DECODE_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValuesExtended/{vin}?format=json"
OPEN_EV_DATA_URL = "https://raw.githubusercontent.com/KilowattApp/open-ev-data/main/data/ev-data.json"
OPEN_EV_DATA_FALLBACK_URL = "https://raw.githubusercontent.com/KilowattApp/open-ev-data/master/data/ev-data.json"

CONF_PRICE_ENTITY = "price_entity"
CONF_CURRENCY = "currency"
CONF_TIME_FORMAT = "time_format"
CONF_DURATION_FORMAT = "duration_format"
CONF_MOTORAPI_KEY = "motorapi_api_key"
CONF_COUNTRY = "country"
CONF_PLATE_PROVIDER = "plate_provider"

COUNTRY_DENMARK = "Denmark"
DEFAULT_COUNTRY = COUNTRY_DENMARK
DEFAULT_PLATE_PROVIDER = "motorapi_dk"

TIME_FORMAT_24H = "24h"
TIME_FORMAT_12H = "12h"
DURATION_FORMAT_MINUTES = "minutes"
DURATION_FORMAT_HM = "hours_minutes"

CURRENCIES = ["DKK", "EUR", "USD"]
TIME_FORMATS = [TIME_FORMAT_24H, TIME_FORMAT_12H]
DURATION_FORMATS = [DURATION_FORMAT_MINUTES, DURATION_FORMAT_HM]
COUNTRIES = [COUNTRY_DENMARK]

INPUT_LICENSE_PLATE = "license_plate"
INPUT_SOC = "soc"
INPUT_BATTERY_CAPACITY = "battery_capacity"
INPUT_CHARGER_POWER = "charger_power"
INPUT_CHARGE_LIMIT = "charge_limit"
INPUT_CHARGE_COMPLETION_TIME = "charge_completion_time"
INPUT_USE_COMPLETION_TIME = "use_completion_time"
INPUT_CONTINUOUS_CHARGING_PREFERRED = "continuous_charging_preferred"

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
ATTR_COUNTRY = "country"
ATTR_PLATE_PROVIDER = "plate_provider"

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.{{entry_id}}"

# Entity removed in 0.7.0 (charger control); cleaned from the entity registry on setup.
LEGACY_ENABLE_CHARGER_CONTROL_KEY = "enable_charger_control"

DATASET_CACHE_KEY = f"{DOMAIN}_open_ev_data_cache"

SERVICE_GRAB_CAR_DATA = "grab_car_data"
SERVICE_CALCULATE = "calculate"

REDACT_KEYS = {CONF_MOTORAPI_KEY, ATTR_VIN, INPUT_LICENSE_PLATE}
