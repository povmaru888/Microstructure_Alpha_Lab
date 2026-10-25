from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_report_contains_method_failure_cases_and_honest_limitations() -> None:
    report = (ROOT / "reports/research_report.md").read_text(encoding="utf-8")
    for heading in (
        "Research question",
        "Quality pipeline",
        "Feature definitions",
        "Labels and leakage",
        "Models and evaluation",
        "Failure cases and limitations",
    ):
        assert heading in report
    assert "Single-day empirical results" in report
    assert "not evidence of out-of-day alpha" in report
    assert "cross-day alpha" in report
    assert "materially slower than vectorisation" in report
    assert len(report.split()) >= 900
