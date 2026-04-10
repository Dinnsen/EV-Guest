from custom_components.ev_guest.const import INPUT_CHARGE_LIMIT, INPUT_CHARGER_POWER, INPUT_SOC
from custom_components.ev_guest.number import NUMBER_SPECS


def test_required_number_inputs_present():
    assert INPUT_SOC in NUMBER_SPECS
    assert INPUT_CHARGER_POWER in NUMBER_SPECS
    assert INPUT_CHARGE_LIMIT in NUMBER_SPECS
