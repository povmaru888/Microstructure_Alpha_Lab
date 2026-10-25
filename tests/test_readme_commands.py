import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_readme_commands_match_actual_clis() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for script in (
        "scripts/prepare_data.py",
        "scripts/run_experiment.py",
        "scripts/run_benchmark.py",
        "scripts/evaluate_run.py",
    ):
        assert script in readme
        completed = subprocess.run(
            [sys.executable, ROOT / script, "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
    assert "Do not commit or redistribute" in readme
    assert "not a live trading system" in readme
