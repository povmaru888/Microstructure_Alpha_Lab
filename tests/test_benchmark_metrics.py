import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from microalpha.benchmark import measure_stage


def test_timer_records_five_raw_perf_counter_samples() -> None:
    result = measure_stage(lambda: sum(range(10)), repeats=5, warmups=1)
    assert result["clock"] == "time.perf_counter"
    assert len(result["raw_seconds"]) == 5
    assert all(value >= 0 for value in result["raw_seconds"])
    with pytest.raises(ValueError, match="at least 5"):
        measure_stage(lambda: None, repeats=4)


def test_cpp_cli_emits_segmented_steady_clock_timings(tmp_path: Path, cpp_binary: Path) -> None:
    source = tmp_path / "input.csv"
    output = tmp_path / "output.csv"
    source.write_text(
        "dataset_id,event_index,research_index,ask_price_1,ask_size_1,bid_price_1,bid_size_1\nd,0,0,101,300,99,900\n",
        encoding="utf-8",
    )
    completed = subprocess.run(
        [cpp_binary, "--input", source, "--output", output, "--levels", "1", "--timing"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    assert "TIMING parse=" in completed.stderr
    assert " compute=" in completed.stderr and " write=" in completed.stderr


def test_benchmark_cli_writes_all_implementations(
    synthetic_books: pd.DataFrame, tmp_path: Path, cpp_binary: Path
) -> None:
    input_path = tmp_path / "validated.parquet"
    synthetic_books.to_parquet(input_path, index=False)
    root = Path(__file__).parents[1]
    completed = subprocess.run(
        [
            sys.executable,
            root / "scripts/run_benchmark.py",
            "--input",
            input_path,
            "--run-id",
            "bench",
            "--output-dir",
            tmp_path,
            "--cpp-binary",
            cpp_binary,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    raw = json.loads((tmp_path / "bench/benchmark_raw.json").read_text(encoding="utf-8"))
    assert {"python_parse", "python_loop_compute", "numpy_compute", "python_write", "cpp"} <= set(
        raw
    )
    assert len(raw["cpp"]["parse_seconds"]) == 5
    report = json.loads((tmp_path / "bench/benchmark_report.json").read_text(encoding="utf-8"))
    assert report["parity"]["status"] == "passed"
