import json
from pathlib import Path


def test_hacs_json_has_domain_and_name():
    data = json.loads((Path(__file__).resolve().parents[1] / 'hacs.json').read_text(encoding='utf-8'))
    assert data['name'] == 'EV Guest'
    assert data['domains'] == ['ev_guest']
