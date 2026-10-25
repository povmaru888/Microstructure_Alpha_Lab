import hashlib
from datetime import date
from pathlib import Path

import pytest

from microalpha.artifacts import build_data_manifest
from microalpha.config import SourceConfig


def _source(message: Path, orderbook: Path) -> SourceConfig:
    return SourceConfig(
        provider="lobster",
        dataset_id="synthetic_l2",
        symbol="TEST",
        trade_date=date(2026, 1, 2),
        levels=2,
        price_scale=10_000,
        message_path=message,
        orderbook_path=orderbook,
    )


def test_manifest_uses_real_hashes_and_counts(fixture_dir: Path) -> None:
    message = fixture_dir / "message.csv"
    orderbook = fixture_dir / "orderbook_l2.csv"
    manifest = build_data_manifest(
        _source(message, orderbook),
        source_page="https://example.test/official",
        license_note="Synthetic fixture only",
    )
    assert manifest["dataset_id"] == "synthetic_l2"
    assert manifest["files"]["message"]["rows"] == 6
    assert (
        manifest["files"]["message"]["sha256"] == hashlib.sha256(message.read_bytes()).hexdigest()
    )
    assert manifest["downloaded_at_utc"] is None


def test_manifest_fails_on_missing_file(fixture_dir: Path) -> None:
    with pytest.raises(FileNotFoundError, match="required input"):
        build_data_manifest(
            _source(fixture_dir / "missing.csv", fixture_dir / "orderbook_l2.csv"),
            source_page="https://example.test",
            license_note="fixture",
        )


def test_manifest_fails_on_hash_mismatch(fixture_dir: Path) -> None:
    with pytest.raises(ValueError, match="SHA-256 mismatch for message"):
        build_data_manifest(
            _source(fixture_dir / "message.csv", fixture_dir / "orderbook_l2.csv"),
            source_page="https://example.test",
            license_note="fixture",
            expected_hashes={"message": "0" * 64},
        )
