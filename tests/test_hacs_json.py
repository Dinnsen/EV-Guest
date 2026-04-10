import json
from pathlib import Path


def test_hacs_json_shape():
    data = json.loads(Path('hacs.json').read_text())
    assert data['country'] == 'DK'
    assert data['homeassistant'] == '2026.3.0'
