"""Parity and benchmark helpers."""

import os
import platform
import subprocess
import sys
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter

import numpy as np
import pandas as pd

from microalpha.artifacts import sha256_file

FEATURE_COLUMNS = [
    "midprice",
    "spread",
    "relative_spread",
    "obi_l1",
    "obi_l5",
    "obi_l10",
    "microprice",
    "micro_deviation",
    "ofi_event",
    "ofi_w10",
    "ofi_w20",
    "ofi_w50",
]


def python_loop_features(books: pd.DataFrame) -> pd.DataFrame:
    rows = []
    events: deque[float] = deque(maxlen=50)
    previous = None
    for record in books.itertuples(index=False):
        row = {"dataset_id": record.dataset_id, "event_index": record.event_index}
        bid, ask = record.bid_price_1, record.ask_price_1
        mid = (bid + ask) / 2
        row.update(midprice=mid, spread=ask - bid, relative_spread=(ask - bid) / mid)
        for depth in (1, 5, 10):
            bid_total = sum(getattr(record, f"bid_size_{level}") for level in range(1, depth + 1))
            ask_total = sum(getattr(record, f"ask_size_{level}") for level in range(1, depth + 1))
            row[f"obi_l{depth}"] = (
                (bid_total - ask_total) / (bid_total + ask_total)
                if bid_total + ask_total > 0
                else np.nan
            )
        total = record.bid_size_1 + record.ask_size_1
        row["microprice"] = (
            (ask * record.bid_size_1 + bid * record.ask_size_1) / total if total > 0 else np.nan
        )
        row["micro_deviation"] = (row["microprice"] - mid) / mid if total > 0 else np.nan
        event = np.nan
        if previous is not None:
            event = (
                (bid >= previous.bid_price_1) * record.bid_size_1
                - (bid <= previous.bid_price_1) * previous.bid_size_1
                - (ask <= previous.ask_price_1) * record.ask_size_1
                + (ask >= previous.ask_price_1) * previous.ask_size_1
            )
            events.append(float(event))
        row["ofi_event"] = event
        for window in (10, 20, 50):
            row[f"ofi_w{window}"] = sum(list(events)[-window:]) if len(events) >= window else np.nan
        rows.append(row)
        previous = record
    return pd.DataFrame(rows)


@dataclass
class ParityError(AssertionError):
    differences: list[dict]
    exit_code: int = 6

    def __str__(self) -> str:
        return f"Python/C++ parity failed ({len(self.differences)} shown differences)"


def compare_features(python: pd.DataFrame, cpp: pd.DataFrame) -> dict:
    merged = python.merge(
        cpp, on=["dataset_id", "event_index"], suffixes=("_py", "_cpp"), validate="one_to_one"
    )
    if len(merged) != len(python) or len(merged) != len(cpp):
        raise ParityError([{"reason": "event key mismatch"}])
    differences = []
    for column in FEATURE_COLUMNS:
        left, right = merged[f"{column}_py"], merged[f"{column}_cpp"]
        null_mismatch = left.isna() != right.isna()
        numeric_mismatch = ~(
            np.isclose(left, right, atol=1e-9, rtol=1e-8) | (left.isna() & right.isna())
        )
        for index in merged.index[null_mismatch | numeric_mismatch]:
            differences.append(
                {
                    "event_index": int(merged.loc[index, "event_index"]),
                    "feature": column,
                    "python": left.loc[index],
                    "cpp": right.loc[index],
                }
            )
            if len(differences) == 20:
                raise ParityError(differences)
    if differences:
        raise ParityError(differences)
    return {
        "rows": len(merged),
        "features": len(FEATURE_COLUMNS),
        "tolerance": "1e-9 + 1e-8*abs(ref)",
        "status": "passed",
    }


def measure_stage(function: Callable[[], object], *, repeats: int = 5, warmups: int = 1) -> dict:
    if repeats < 5 or warmups < 0:
        raise ValueError("benchmark requires at least 5 repeats and nonnegative warmups")
    for _ in range(warmups):
        function()
    samples = []
    for _ in range(repeats):
        started = perf_counter()
        function()
        samples.append(perf_counter() - started)
    return {
        "clock": "time.perf_counter",
        "warmups": warmups,
        "repeats": repeats,
        "raw_seconds": samples,
    }


def benchmark_environment(
    input_path: str, *, build_type: str = "Release", threads: int = 1
) -> dict:
    try:
        compiler = subprocess.run(
            ["c++", "--version"], check=True, capture_output=True, text=True
        ).stdout.splitlines()[0]
    except (OSError, subprocess.SubprocessError):
        compiler = None
    return {
        "os": platform.platform(),
        "cpu": platform.processor() or "unknown",
        "python": sys.version.split()[0],
        "compiler": compiler,
        "build_type": build_type,
        "compiler_flags": "CMake Release flags recorded by generated build",
        "threads": threads,
        "input_sha256": sha256_file(input_path),
        "peak_rss_method": "resource.getrusage(RUSAGE_SELF).ru_maxrss; runner platform units",
        "process_id_recorded": os.getpid() is not None,
    }


def comparable(environments: list[dict]) -> tuple[bool, list[str]]:
    reasons = []
    if any(item.get("build_type") != "Release" for item in environments):
        reasons.append("non_release_build")
    if any(item.get("threads") != 1 for item in environments):
        reasons.append("not_single_threaded")
    if len({item.get("input_sha256") for item in environments}) != 1:
        reasons.append("input_hash_mismatch")
    return not reasons, reasons


def benchmark_report(
    raw: dict[str, dict], *, records: int, environment: dict, parity: dict
) -> dict:
    implementations = {}
    for name, measurement in raw.items():
        samples = measurement.get("raw_seconds")
        if not samples:
            implementations[name] = None
            continue
        values = np.asarray(samples, dtype=float)
        median = float(np.median(values))
        implementations[name] = {
            "raw_seconds": values.tolist(),
            "median_seconds": median,
            "min_seconds": float(values.min()),
            "max_seconds": float(values.max()),
            "iqr_seconds": float(np.percentile(values, 75) - np.percentile(values, 25)),
            "records_per_second": records / median if median > 0 else None,
            "peak_rss": measurement.get("peak_rss"),
        }
    return {
        "schema_version": "1.0",
        "records": records,
        "environment": environment,
        "parity": parity,
        "implementations": implementations,
        "speedups": None,
        "note": "Speedups remain null unless all implementations were measured comparably.",
    }
