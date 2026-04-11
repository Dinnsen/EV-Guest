"""Constants for EV Guest."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "ev_guest"
DEFAULT_NAME = "EV Guest"
PLATFORMS = [
    "sensor",
    "button",
    "number",
    "text",
    "switch",
    "binary_sensor",
]
DEFAULT_SCAN_INTERVAL = timedelta(minutes=30)
CONTROL_VERIFY_INTERVAL = timedelta(minutes=5)
USER_AGENT = "EVGuestHomeAssistant/0.5.0 (+https://github.com/Dinnsen/EV-Guest)"

MOTORAPI_BASE_URL = "https://v1.motorapi.dk"
NHTSA_DECODE_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValuesExtended/{vin}?format=json"
OPEN_EV_DATA_URL = "https://raw.githubusercontent.com/KilowattApp/open-ev-data/main/data/ev-data.json"
OPEN_EV_DATA_FALLBACK_URL = "https://raw.githubusercontent.com/KilowattApp/open-ev-data/master/data/ev-data.json"

CONF_PRICE_ENTITY = "price_entity"
CONF_CURRENCY = "currency"
CONF_TIME_FORMAT = "time_format"
CONF_DURATION_FORMAT = "duration_format"
CONF_MOTORAPI_KEY = "motorapi_api_key"
CONF_CHARGER_SWITCH_ENTITY = "charger_switch_entity"
CONF_CHARGER_BACKEND = "charger_backend"
CONF_CHARGER_STATUS_ENTITY = "charger_status_entity"
CONF_CHARGER_START_SERVICE = "charger_start_service"
CONF_CHARGER_STOP_SERVICE = "charger_stop_service"
CONF_CHARGER_START_DATA = "charger_start_data"
CONF_CHARGER_STOP_DATA = "charger_stop_data"
CONF_LANGUAGE = "language"
CONF_COUNTRY = "country"

LANGUAGE_EN = "en"
LANGUAGE_DA = "da"
LANGUAGES = [LANGUAGE_EN, LANGUAGE_DA]

COUNTRY_DK = "dk"
COUNTRIES = [COUNTRY_DK]

PLATE_PROVIDER_MOTORAPI_DK = "motorapi_dk"
COUNTRY_PROVIDER_DEFAULTS = {
    COUNTRY_DK: PLATE_PROVIDER_MOTORAPI_DK,
}

CHARGER_BACKEND_GENERIC = "generic_switch"
CHARGER_BACKEND_OK = "ok"
CHARGER_BACKEND_EASEE = "easee"
CHARGER_BACKEND_ZAPTEC_GO = "zaptec_go"
CHARGER_BACKEND_TESLA_WALL_CONNECTOR = "tesla_wall_connector"
CHARGER_BACKEND_HA_EV_SMART_CHARGING = "ha_ev_smart_charging"
CHARGER_BACKEND_DUMMY = "dummy_test"

CHARGER_BACKENDS = [
    CHARGER_BACKEND_GENERIC,
    CHARGER_BACKEND_OK,
    CHARGER_BACKEND_EASEE,
    CHARGER_BACKEND_ZAPTEC_GO,
    CHARGER_BACKEND_TESLA_WALL_CONNECTOR,
    CHARGER_BACKEND_HA_EV_SMART_CHARGING,
    CHARGER_BACKEND_DUMMY,
]

BACKENDS_REQUIRING_SWITCH = {
    CHARGER_BACKEND_GENERIC,
    CHARGER_BACKEND_OK,
    CHARGER_BACKEND_EASEE,
    CHARGER_BACKEND_ZAPTEC_GO,
    CHARGER_BACKEND_TESLA_WALL_CONNECTOR,
}

TIME_FORMAT_24H = "24h"
TIME_FORMAT_12H = "12h"
DURATION_FORMAT_MINUTES = "minutes"
DURATION_FORMAT_HM = "hours_minutes"
CURRENCIES = ["DKK", "EUR", "USD"]
TIME_FORMATS = [TIME_FORMAT_24H, TIME_FORMAT_12H]
DURATION_FORMATS = [DURATION_FORMAT_MINUTES, DURATION_FORMAT_HM]

INPUT_LICENSE_PLATE = "license_plate"
INPUT_SOC = "soc"
INPUT_BATTERY_CAPACITY = "battery_capacity"
INPUT_CHARGER_POWER = "charger_power"
INPUT_CHARGE_LIMIT = "charge_limit"
INPUT_CHARGE_COMPLETION_TIME = "charge_completion_time"
INPUT_USE_COMPLETION_TIME = "use_completion_time"
INPUT_ENABLE_CHARGER_CONTROL = "enable_charger_control"
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

RESULT_CHARGER_BACKEND = "charger_backend"
RESULT_CHARGER_TARGET_STATE = "charger_target_state"
RESULT_CHARGER_ACTUAL_STATE = "charger_actual_state"
RESULT_CHARGER_LAST_COMMAND = "charger_last_command"
RESULT_CHARGER_LAST_RESULT = "charger_last_result"
RESULT_CHARGER_NEXT_START = "charger_next_start"
RESULT_CHARGER_NEXT_STOP = "charger_next_stop"
RESULT_CHARGER_ACTIVE_WINDOW = "charger_active_window"

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
ATTR_CHARGER_CONTROL_ENABLED = "charger_control_enabled"
ATTR_CHARGER_ENTITY = "charger_entity"
ATTR_CHARGER_STATUS_ENTITY = "charger_status_entity"
ATTR_CHARGER_BACKEND = "charger_backend"
ATTR_CHARGER_COMMANDABLE = "charger_commandable"
ATTR_CHARGER_EXPECTED_ON = "charger_expected_on"
ATTR_CHARGER_ACTUAL_ON = "charger_actual_on"
ATTR_CHARGER_MISMATCH = "charger_mismatch"
ATTR_LAST_CHARGER_COMMAND_AT = "last_charger_command_at"
ATTR_LAST_CHARGER_COMMAND_REASON = "last_charger_command_reason"
ATTR_CONTROL_TICK_INTERVAL = "control_tick_interval"
ATTR_DUMMY_CHARGER = "dummy_charger"
ATTR_LANGUAGE = "language"
ATTR_COUNTRY = "country"
ATTR_PLATE_PROVIDER = "plate_provider"

DATASET_CACHE_KEY = f"{DOMAIN}_open_ev_data_cache"
SERVICE_GRAB_CAR_DATA = "grab_car_data"
SERVICE_CALCULATE = "calculate"
SERVICE_FORCE_START_CHARGER = "force_start_charger"
SERVICE_FORCE_STOP_CHARGER = "force_stop_charger"
SERVICE_RESYNC_CHARGER_PLAN = "resync_charger_plan"

REDACT_KEYS = {CONF_MOTORAPI_KEY, ATTR_VIN, INPUT_LICENSE_PLATE}
