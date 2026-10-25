from pathlib import Path

from microalpha.benchmark import benchmark_environment, comparable


def test_environment_records_hash_and_comparability(tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    source.write_text("x\n1\n", encoding="utf-8")
    environment = benchmark_environment(str(source))
    assert len(environment["input_sha256"]) == 64
    assert environment["build_type"] == "Release"
    assert environment["threads"] == 1
    assert comparable([environment, environment]) == (True, [])
    changed = {**environment, "threads": 2, "input_sha256": "0" * 64}
    ok, reasons = comparable([environment, changed])
    assert not ok
    assert {"not_single_threaded", "input_hash_mismatch"} <= set(reasons)
