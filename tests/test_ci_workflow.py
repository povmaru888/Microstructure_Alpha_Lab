from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_ci_runs_python_cpp_and_parity_without_raw_data() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    for command in (
        "ruff check .",
        "python -m pip install --no-deps -e .",
        "ruff format --check .",
        "cmake -S cpp -B cpp/build -DCMAKE_BUILD_TYPE=Release",
        "ctest --test-dir cpp/build --output-on-failure -C Release",
        "pytest -q",
    ):
        assert command in workflow
    assert "data/raw" not in workflow
    assert "ubuntu-24.04" in workflow
    assert "push:" in workflow and "pull_request:" in workflow
