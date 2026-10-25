"""LOBSTER CSV ingestion preserving positional event alignment."""

from pathlib import Path

import pandas as pd

from microalpha.config import SourceConfig

MESSAGE_COLUMNS = ("time_seconds", "event_type", "order_id", "size", "price", "direction")


class IngestError(ValueError):
    pass


def _book_columns(levels: int) -> list[str]:
    return [
        f"{field}_{level}"
        for level in range(1, levels + 1)
        for field in ("ask_price", "ask_size", "bid_price", "bid_size")
    ]


def ingest_lobster(config: SourceConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Parse headerless LOBSTER files without sorting or joining on timestamps."""
    for path in (config.message_path, config.orderbook_path):
        if not Path(path).is_file():
            raise FileNotFoundError(f"required raw file does not exist: {path}")
    events = pd.read_csv(config.message_path, header=None, names=MESSAGE_COLUMNS)
    books = pd.read_csv(config.orderbook_path, header=None, names=_book_columns(config.levels))
    if len(events) != len(books):
        raise IngestError(f"row count mismatch: message={len(events)}, orderbook={len(books)}")
    if events.shape[1] != 6 or books.shape[1] != config.levels * 4:
        raise IngestError("unexpected raw column count")
    if events.isna().any(axis=None) or books.isna().any(axis=None):
        raise IngestError("missing or malformed raw fields")
    event_index = pd.RangeIndex(len(events), name="event_index")
    events.index = event_index
    books.index = event_index
    for frame in (events, books):
        frame.insert(0, "dataset_id", config.dataset_id)
        frame.insert(1, "event_index", event_index.astype("int64"))
    events = events.astype(
        {
            "event_type": "int8",
            "order_id": "int64",
            "size": "int64",
            "price": "int64",
            "direction": "int8",
        }
    )
    price_columns = [name for name in books if "_price_" in name]
    size_columns = [name for name in books if "_size_" in name]
    books[price_columns] = books[price_columns].astype("float64") / config.price_scale
    books[size_columns] = books[size_columns].astype("float64")
    events["price_raw"] = events["price"]
    events["price"] = events["price"].astype("float64") / config.price_scale
    events["raw_row_index"] = event_index.astype("int64")
    books["raw_row_index"] = event_index.astype("int64")
    return events.reset_index(drop=True), books.reset_index(drop=True)
