from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_executive_summary_covers_interview_story_in_one_page() -> None:
    summary = (ROOT / "reports/executive_summary.md").read_text(encoding="utf-8")
    for heading in (
        "Question",
        "Data and integrity boundary",
        "Method",
        "Verified findings",
        "Failure cases and limitations",
        "Three-minute takeaway",
    ):
        assert heading in summary
    assert "400,391 aligned rows" in summary
    assert "not general alpha" in summary
    assert 350 <= len(summary.split()) <= 800
