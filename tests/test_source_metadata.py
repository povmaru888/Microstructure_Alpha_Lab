from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]


def _metadata() -> dict:
    return yaml.safe_load((ROOT / "docs/source_metadata.yaml").read_text(encoding="utf-8"))


def test_official_sample_identity_and_format_are_recorded() -> None:
    metadata = _metadata()
    sample = metadata["sample"]
    assert sample["symbol"] == "AAPL"
    assert sample["trade_date"] == "2012-06-21"
    assert sample["levels"] == 10
    assert sample["archive_filename"] == "LOBSTER_SampleFile_AAPL_2012-06-21_10.zip"
    assert sample["downloaded"] is True
    assert sample["rows"] == 400_391
    assert len(sample["message_sha256"]) == 64
    assert len(sample["orderbook_sha256"]) == 64
    assert metadata["format"]["price_scale"] == 10_000
    assert set(metadata["format"]["event_types"]) == set(range(1, 8))


def test_market_rules_are_source_verified() -> None:
    metadata = _metadata()
    assert metadata["market_rules"]["tick_size"] == 0.01
    assert metadata["market_rules"]["sample_session_seconds"] == [34_200, 57_600]
    assert "Rule 612" in metadata["market_rules"]["note"]
    assert metadata["market_rules"]["tick_source"].startswith("https://www.sec.gov/")


def test_raw_redistribution_is_prohibited_by_repository_policy() -> None:
    metadata = _metadata()
    assert metadata["redistribution"]["raw_files_committable"] is False
    assert "prohibit redistribution" in metadata["redistribution"]["note"]
    assert "data/raw/**" in (ROOT / ".gitignore").read_text(encoding="utf-8")
