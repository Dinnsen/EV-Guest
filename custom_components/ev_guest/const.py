"""Constants for EV Guest."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "ev_guest"
DEFAULT_NAME = "EV Guest"
DEFAULT_SCAN_INTERVAL = timedelta(minutes=15)
USER_AGENT = "Mozilla/5.0 (compatible; EVGuestHomeAssistant/0.2.0; +https://github.com/Dinnsen/EV-Guest)"

MOTORAPI_BASE_URL = "https://v1.motorapi.dk"
NHTSA_DECODE_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValuesExtended/{vin}?format=json"
OPEN_EV_DATA_URL = "https://raw.githubusercontent.com/KilowattApp/open-ev-data/master/data/ev-data.json"

CONF_PRICE_ENTITY = "price_entity"
CONF_CURRENCY = "currency"
CONF_TIME_FORMAT = "time_format"
CONF_DURATION_FORMAT = "duration_format"
CONF_MOTORAPI_KEY = "motorapi_api_key"

TIME_FORMAT_24H = "24h"
TIME_FORMAT_12H = "12h"
DURATION_FORMAT_MINUTES = "minutes"
DURATION_FORMAT_HM = "hours_minutes"

CURRENCIES = ["DKK", "EUR", "USD"]
TIME_FORMATS = [TIME_FORMAT_24H, TIME_FORMAT_12H]
DURATION_FORMATS = [DURATION_FORMAT_MINUTES, DURATION_FORMAT_HM]

ATTR_BRAND = "car_brand"
ATTR_MODEL = "car_model"
ATTR_VARIANT = "car_variant"
ATTR_BATTERY_CAPACITY = "car_battery_capacity"
ATTR_STATUS = "status"
ATTR_LAST_LOOKUP = "last_lookup"
ATTR_LAST_CALCULATION = "last_calculation"
ATTR_LAST_SOURCE = "last_source"
ATTR_VIN = "vin"
ATTR_MODEL_YEAR = "model_year"
ATTR_FUEL_TYPE = "fuel_type"

DATA_INPUTS = "inputs"
DATA_RESULTS = "results"

INPUT_LICENSE_PLATE = "license_plate"
INPUT_SOC = "soc"
INPUT_BATTERY_CAPACITY = "battery_capacity"
INPUT_CHARGER_POWER = "charger_power"
INPUT_CHARGE_LIMIT = "charge_limit"
INPUT_CHARGE_COMPLETION_TIME = "charge_completion_time"

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
