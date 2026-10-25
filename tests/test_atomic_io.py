from pathlib import Path

import pandas as pd
import pytest

from microalpha.artifacts import atomic_write_parquet


def test_atomic_parquet_success(tmp_path: Path) -> None:
    target = tmp_path / "out.parquet"
    atomic_write_parquet(target, pd.DataFrame({"x": [1, 2]}))
    assert pd.read_parquet(target)["x"].tolist() == [1, 2]


def test_atomic_parquet_failure_leaves_no_output(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "out.parquet"

    def fail(*args, **kwargs):
        raise RuntimeError("write failed")

    monkeypatch.setattr(pd.DataFrame, "to_parquet", fail)
    with pytest.raises(RuntimeError, match="write failed"):
        atomic_write_parquet(target, pd.DataFrame({"x": [1]}))
    assert not target.exists()
    assert list(tmp_path.iterdir()) == []
