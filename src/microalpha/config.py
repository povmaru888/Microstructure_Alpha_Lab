"""Typed experiment configuration with cross-section validation."""

from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, PositiveFloat, PositiveInt, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ProjectConfig(StrictModel):
    name: str
    seed: int = 42
    output_root: Path = Path("artifacts")


class SourceConfig(StrictModel):
    provider: Literal["lobster"]
    dataset_id: str
    symbol: str
    trade_date: date
    levels: PositiveInt
    price_scale: PositiveInt
    message_path: Path
    orderbook_path: Path


class QualityConfig(StrictModel):
    exclude_locked: bool = True
    exclude_crossed: bool = True
    market_hours_policy: Literal["provider_regular_session", "none"]


class FeatureConfig(StrictModel):
    depths: tuple[PositiveInt, ...] = (1, 5, 10)
    ofi_windows: tuple[PositiveInt, ...] = (10, 20, 50)
    depth_weights: Literal["equal"] = "equal"


class LabelConfig(StrictModel):
    horizons: tuple[PositiveInt, ...] = (10, 20, 50)
    threshold_mode: Literal["half_tick_over_mid", "fixed_return"]
    tick_size: PositiveFloat | None = None
    fixed_return_threshold: PositiveFloat | None = None

    @model_validator(mode="after")
    def validate_threshold_input(self) -> "LabelConfig":
        if self.threshold_mode == "half_tick_over_mid" and self.tick_size is None:
            raise ValueError("labels.tick_size is required for half_tick_over_mid")
        if self.threshold_mode == "fixed_return" and self.fixed_return_threshold is None:
            raise ValueError("labels.fixed_return_threshold is required for fixed_return")
        return self


class SplitConfig(StrictModel):
    method: Literal["chronological_purged"]
    train_frac: float = Field(gt=0, lt=1)
    valid_frac: float = Field(gt=0, lt=1)

    @model_validator(mode="after")
    def leave_nonempty_test_fraction(self) -> "SplitConfig":
        if self.train_frac + self.valid_frac >= 1:
            raise ValueError("train_frac + valid_frac must be less than 1")
        return self


class ModelConfig(StrictModel):
    enabled: tuple[Literal["majority", "obi_rule", "logistic", "xgboost"], ...]
    random_state: int = 42


class BenchmarkConfig(StrictModel):
    repeats: PositiveInt = 5
    warmups: int = Field(default=1, ge=0)


class Settings(StrictModel):
    project: ProjectConfig
    source: SourceConfig
    quality: QualityConfig
    features: FeatureConfig
    labels: LabelConfig
    split: SplitConfig
    models: ModelConfig
    benchmark: BenchmarkConfig

    @model_validator(mode="after")
    def validate_available_depth(self) -> "Settings":
        if max(self.features.depths) > self.source.levels:
            raise ValueError("feature depth cannot exceed source levels")
        return self


def load_settings(path: str | Path) -> Settings:
    """Load YAML from *path* and validate all sections."""
    config_path = Path(path)
    with config_path.open(encoding="utf-8") as stream:
        payload = yaml.safe_load(stream)
    if not isinstance(payload, dict):
        raise ValueError("configuration root must be a mapping")
    return Settings.model_validate(payload)
