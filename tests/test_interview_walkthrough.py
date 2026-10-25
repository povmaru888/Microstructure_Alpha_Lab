from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_walkthrough_covers_complete_honest_story() -> None:
    document = (ROOT / "reports/interview_walkthrough.md").read_text(encoding="utf-8")
    for topic in (
        "Data provenance",
        "causal research design",
        "Model and evaluation",
        "Python/C++ parity",
        "Performance without benchmark theatre",
        "Limitations",
    ):
        assert topic in document
    for limitation in (
        "not a live HFT system",
        "No broker connection",
        "queue priority",
        "No speedup is promised",
        "Single day",
    ):
        assert limitation in document
