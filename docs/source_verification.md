# LOBSTER source verification

Verified on 2026-10-24 against the provider's official legacy sample and data
structure pages, plus the current trial/sample terms page.

## Confirmed

- The official sample page lists `LOBSTER_SampleFile_AAPL_2012-06-21_10.zip`
  for AAPL, 2012-06-21, depth 10 (listed size 6.5 MB).
- A sample consists of an orderbook file, message file, and README; the page says
  samples derive from the official NASDAQ Historical TotalView-ITCH sample.
- Message rows contain time, event type, order ID, size, price, direction. Event
  types 1–7 and directions -1/+1 are recorded in `source_metadata.yaml`.
- Prices are dollar prices multiplied by 10,000. Each orderbook level is ordered
  ask price, ask size, bid price, bid size.
- Message and orderbook shapes are N×6 and N×(4×levels). Row k of message causes
  the event-after book state at row k, so alignment is positional.
- Empty ask/bid sentinel prices are +9,999,999,999/-9,999,999,999 with volume 0.
  Type-7 halt rows duplicate the prior book state and use documented special values.
- Current trial/sample terms state that download/access means accepting the terms
  and prohibit redistribution, hosting, mirroring, or third-party access unless a
  valid licence expressly permits it. Raw files are therefore gitignored.

## Lawful download verification (2026-10-24)

- The user confirmed acceptance of the current Trial and Sample Data Terms and
  authorised a local, non-redistributed download. The official archive returned
  HTTP 200 and was saved only under gitignored `data/raw/`.
- Archive SHA-256: `326839316d67d7819ca0541ffdf73cdb044d6ae4105cce0ef9c615e8848e9d43`.
- Message/orderbook SHA-256 values, exact filenames, and the common 400,391 row
  count are recorded in `source_metadata.yaml`.
- The README filename convention establishes 34,200,000–57,600,000 milliseconds
  after midnight, i.e. 09:30–16:00.
- Tick size was not inferred from observed gaps. SEC Regulation NMS Rule 612,
  Release 34-51808, states that NMS bids/offers/orders priced at least $1 may not
  use increments smaller than $0.01. The AAPL sample quotes are well above $1, so
  the run-specific half-tick label configuration records `tick_size: 0.01`.

## Manual lawful-download checklist

1. Review and accept the terms shown by the provider account/download flow.
2. Record terms version, source URL, UTC download time, archive filename/hash.
3. Inspect the included README; record internal filenames and exact session.
4. Compute both CSV hashes and row counts without changing either raw file.
5. Verify a reliable venue tick-size rule separately; never infer it from test scores.

