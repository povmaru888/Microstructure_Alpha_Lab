from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from microalpha.config import Settings, load_settings

ROOT = Path(__file__).parents[1]


@pytest.fixture
def valid_payload() -> dict:
    payload = yaml.safe_load((ROOT / "configs/experiment.yaml").read_text(encoding="utf-8"))
    payload["labels"]["tick_size"] = 0.01
    return payload


def test_loads_typed_settings(valid_payload: dict, tmp_path: Path) -> None:
    path = tmp_path / "experiment.yaml"
    path.write_text(yaml.safe_dump(valid_payload), encoding="utf-8")
    settings = load_settings(path)
    assert isinstance(settings, Settings)
    assert settings.source.levels == 10
    assert settings.features.depths == (1, 5, 10)


def test_half_tick_mode_requires_tick_size() -> None:
    with pytest.raises(ValidationError, match="tick_size is required"):
        load_settings(ROOT / "configs/experiment.yaml")


def test_depth_cannot_exceed_source_levels(valid_payload: dict) -> None:
    payload = deepcopy(valid_payload)
    payload["features"]["depths"] = [1, 11]
    with pytest.raises(ValidationError, match="cannot exceed source levels"):
        Settings.model_validate(payload)


def test_unknown_settings_are_rejected(valid_payload: dict) -> None:
    payload = deepcopy(valid_payload)
    payload["source"]["unrecognized"] = True
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        Settings.model_validate(payload)
