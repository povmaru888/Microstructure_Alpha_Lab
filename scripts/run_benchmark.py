#!/usr/bin/env python3
"""Run segmented, repeatable Python feature benchmarks."""

import argparse
import re
import subprocess
import tempfile
from pathlib import Path

import pandas as pd

from microalpha.artifacts import atomic_write_json, refresh_run_manifest
from microalpha.benchmark import (
    benchmark_environment,
    benchmark_report,
    compare_features,
    measure_stage,
    python_loop_features,
)
from microalpha.config import FeatureConfig
from microalpha.features import compute_features


def _canonical(frame: pd.DataFrame) -> pd.DataFrame:
    eligible = frame[frame["eligible"]].copy() if "eligible" in frame else frame.copy()
    levels = max(int(name.rsplit("_", 1)[1]) for name in eligible if name.startswith("bid_size_"))
    columns = ["dataset_id", "event_index", "research_index"] + [
        f"{field}_{level}"
        for level in range(1, levels + 1)
        for field in ("ask_price", "ask_size", "bid_price", "bid_size")
    ]
    return eligible[columns].reset_index(drop=True)


def _cpp_samples(
    binary: Path, source: Path, output: Path, repeats: int, warmups: int, levels: int
) -> dict:
    samples = {"parse_seconds": [], "compute_seconds": [], "write_seconds": []}
    pattern = re.compile(r"TIMING parse=([\d.eE+-]+) compute=([\d.eE+-]+) write=([\d.eE+-]+)")
    for iteration in range(warmups + repeats):
        completed = subprocess.run(
            [
                binary,
                "--input",
                source,
                "--output",
                output,
                "--levels",
                str(levels),
                "--force",
                "--timing",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        match = pattern.search(completed.stderr)
        if not match:
            raise RuntimeError("C++ timing output missing")
        if iteration >= warmups:
            for name, value in zip(samples, match.groups(), strict=True):
                samples[name].append(float(value))
    combined = [sum(values) for values in zip(*samples.values(), strict=True)]
    return {
        "clock": "std::chrono::steady_clock",
        "warmups": warmups,
        "repeats": repeats,
        "raw_seconds": combined,
        **samples,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--cpp-binary", type=Path, default=Path("cpp/build/microalpha_features"))
    args = parser.parse_args()
    frame = pd.read_parquet(args.input)
    canonical = _canonical(frame)
    levels = max(int(name.rsplit("_", 1)[1]) for name in canonical if name.startswith("bid_size_"))
    feature_config = FeatureConfig(depths=tuple(depth for depth in (1, 5, 10) if depth <= levels))
    run_dir = args.output_dir / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary_text:
        temporary = Path(temporary_text)
        csv_path, cpp_output = temporary / "canonical.csv", temporary / "cpp.csv"
        canonical.to_csv(csv_path, index=False)
        compute_input = canonical.assign(eligible=True)
        raw = {
            "python_parse": measure_stage(
                lambda: pd.read_csv(csv_path), repeats=args.repeats, warmups=args.warmups
            ),
            "python_loop_compute": measure_stage(
                lambda: python_loop_features(compute_input),
                repeats=args.repeats,
                warmups=args.warmups,
            ),
            "numpy_compute": measure_stage(
                lambda: compute_features(compute_input, feature_config),
                repeats=args.repeats,
                warmups=args.warmups,
            ),
            "python_write": measure_stage(
                lambda: compute_features(compute_input, feature_config).to_csv(
                    temporary / "python.csv", index=False
                ),
                repeats=args.repeats,
                warmups=args.warmups,
            ),
            "cpp": _cpp_samples(
                args.cpp_binary, csv_path, cpp_output, args.repeats, args.warmups, levels
            ),
        }
        parity = compare_features(
            compute_features(compute_input, feature_config), pd.read_csv(cpp_output)
        )
        environment = benchmark_environment(str(csv_path))
        summary_input = {
            name: measurement for name, measurement in raw.items() if "raw_seconds" in measurement
        }
        report = benchmark_report(
            summary_input, records=len(canonical), environment=environment, parity=parity
        )
        report["segmented_raw"] = raw
    atomic_write_json(run_dir / "benchmark_raw.json", raw)
    atomic_write_json(run_dir / "benchmark_report.json", report)
    refresh_run_manifest(run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
