from pathlib import Path

import pandas as pd
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_dir() -> Path:
    return FIXTURES


@pytest.fixture
def cpp_binary() -> Path:
    root = Path(__file__).parents[1]
    candidates = (
        root / "cpp/build/microalpha_features",
        root / "cpp/build/microalpha_features.exe",
        root / "cpp/build/Release/microalpha_features.exe",
    )
    binary = next((path for path in candidates if path.is_file()), None)
    assert binary is not None, f"C++ binary not found in: {candidates}"
    return binary


@pytest.fixture
def synthetic_books() -> pd.DataFrame:
    """A long deterministic sequence suitable for W50 and horizon-50 tests."""
    rows = []
    for index in range(80):
        mid_ticks = 10_000 + index // 10
        row: dict[str, float | int | str | bool] = {
            "dataset_id": "synthetic_l10",
            "event_index": index,
            "research_index": index,
            "time_seconds": 34_200.0 + index / 10,
            "eligible": True,
        }
        for level in range(1, 11):
            row[f"ask_price_{level}"] = (mid_ticks + level) / 100.0
            row[f"ask_size_{level}"] = 300.0 + level + index % 3
            row[f"bid_price_{level}"] = (mid_ticks - level) / 100.0
            row[f"bid_size_{level}"] = 900.0 - level + index % 5
        rows.append(row)
    return pd.DataFrame(rows)
