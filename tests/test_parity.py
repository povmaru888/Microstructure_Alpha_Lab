import os
import subprocess
from pathlib import Path

import pandas as pd

from microalpha.benchmark import compare_features
from microalpha.config import FeatureConfig
from microalpha.features import compute_features


def test_python_cpp_parity(synthetic_books: pd.DataFrame, tmp_path: Path) -> None:
    canonical_columns = ["dataset_id", "event_index", "research_index"] + [
        f"{field}_{level}"
        for level in range(1, 11)
        for field in ("ask_price", "ask_size", "bid_price", "bid_size")
    ]
    source = tmp_path / "canonical.csv"
    output = tmp_path / "cpp.csv"
    synthetic_books[canonical_columns].to_csv(source, index=False)
    binary = Path(__file__).parents[1] / "cpp/build/microalpha_features"
    if os.name == "nt":
        binary = binary.with_suffix(".exe")
    completed = subprocess.run(
        [binary, "--input", source, "--output", output, "--levels", "10"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    python = compute_features(synthetic_books, FeatureConfig())
    cpp = pd.read_csv(output)
    report = compare_features(python, cpp)
    assert report["rows"] == 80
    assert report["status"] == "passed"
