from custom_components.ev_guest.api import clean_identifier, get_default_plate_provider, normalize_text
from custom_components.ev_guest.const import COUNTRY_DK, PLATE_PROVIDER_MOTORAPI_DK


def test_clean_identifier():
    assert clean_identifier('Dn 96-146') == 'DN96146'


def test_normalize_text():
    assert normalize_text('Model 3 Standard+') == 'model3standard+'


def test_default_provider_for_denmark():
    assert get_default_plate_provider(COUNTRY_DK) == PLATE_PROVIDER_MOTORAPI_DK
