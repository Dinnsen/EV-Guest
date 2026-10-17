import json
from pathlib import Path


def test_hacs_json_shape():
    data = json.loads(Path("hacs.json").read_text())
    assert data["country"] == "DK"
    assert data["homeassistant"] == "2026.3.0"


def test_single_integration_manifest():
    """HACS finds the integration by the only file named *manifest.json in the repository."""
    root = Path(__file__).resolve().parent.parent
    manifests = [p for p in root.rglob("*manifest.json") if ".git" not in p.parts and "node_modules" not in p.parts]
    assert [p.relative_to(root).as_posix() for p in manifests] == ["custom_components/ev_guest/manifest.json"]
