from microalpha.benchmark import benchmark_report


def test_report_aggregates_raw_values_without_inventing_missing_results() -> None:
    raw = {"python": {"raw_seconds": [5, 4, 3, 2, 1], "peak_rss": 100}, "cpp": {"raw_seconds": []}}
    report = benchmark_report(
        raw, records=100, environment={"threads": 1}, parity={"status": "passed"}
    )
    python = report["implementations"]["python"]
    assert python["median_seconds"] == 3
    assert python["min_seconds"] == 1
    assert python["max_seconds"] == 5
    assert python["records_per_second"] == 100 / 3
    assert report["implementations"]["cpp"] is None
    assert report["speedups"] is None
