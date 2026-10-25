import csv
from itertools import pairwise
from pathlib import Path


def _read(path: Path) -> list[list[str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return [row for row in csv.reader(stream) if row]


def test_fixture_contains_same_timestamp_and_price_moves(fixture_dir: Path) -> None:
    messages = _read(fixture_dir / "message.csv")
    books = _read(fixture_dir / "orderbook_l2.csv")
    assert messages[0][0] == messages[1][0]
    ask_prices = [int(row[0]) for row in books]
    assert any(right > left for left, right in pairwise(ask_prices))
    assert any(right < left for left, right in pairwise(ask_prices))


def test_fixture_contains_zero_locked_and_crossed_books(fixture_dir: Path) -> None:
    books = _read(fixture_dir / "orderbook_l2.csv")
    assert any(int(row[1]) == 0 or int(row[3]) == 0 for row in books)
    assert any(int(row[0]) == int(row[2]) for row in books)
    assert any(int(row[2]) > int(row[0]) for row in books)


def test_fixture_has_aligned_and_mismatched_variants(fixture_dir: Path) -> None:
    messages = _read(fixture_dir / "message.csv")
    assert len(_read(fixture_dir / "orderbook_l2.csv")) == len(messages)
    assert len(_read(fixture_dir / "orderbook_l2_mismatched.csv")) != len(messages)


def test_fixture_is_small_and_has_no_lobster_payload(fixture_dir: Path) -> None:
    files = list(fixture_dir.glob("*.csv"))
    assert sum(path.stat().st_size for path in files) < 10_000
    assert all("LOBSTER" not in path.read_text(encoding="utf-8") for path in files)
