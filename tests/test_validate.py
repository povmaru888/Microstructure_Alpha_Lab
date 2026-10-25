from test_ingest import _config

from microalpha.config import QualityConfig
from microalpha.ingest import ingest_lobster
from microalpha.validate import validate_lobster


def test_validation_maps_research_index_and_reasons(fixture_dir) -> None:
    source = _config(fixture_dir)
    events, books = ingest_lobster(source)
    validated, report = validate_lobster(
        events,
        books,
        source,
        QualityConfig(exclude_locked=True, exclude_crossed=True, market_hours_policy="none"),
    )
    assert validated.loc[3, "invalid_reason"] == "locked_book"
    assert validated.loc[4, "invalid_reason"] == "crossed_book"
    assert validated.loc[0, "research_index"] == 0
    assert report["raw_rows"] == 6
    assert report["eligible_rows"] + report["excluded_rows"] == 6
