# Microstructure Alpha Lab — Research Report

## Executive scope

This project implements a reproducible experiment for studying whether order-book
imbalance (OBI), quote-change order-flow imbalance (OFI), and Microprice contain
information about short-horizon Midprice direction. It is not an execution system,
does not connect to a broker, and does not establish tradable alpha.

The empirical input is the official LOBSTER AAPL 2012-06-21 depth-10 sample,
downloaded locally after the user confirmed the current sample terms. The two CSVs
contain 400,391 aligned rows covering 09:30–16:00. Raw files remain gitignored and
must not be redistributed. Results are a single-day event-time study and do not
establish return, cross-day generalisation, or tradable alpha.

## Research question and hypotheses

The target is the direction of Midprice after 10, 20, or 50 eligible order-book
updates. The working hypotheses are that positive OBI and Microprice deviation may
precede upward Midprice changes, while accumulated positive quote OFI may capture
net pressure at the best quotes. These are hypotheses, not conclusions.

The three-class label compares the future log Midprice return with a half-tick over
current-Midprice threshold. Tick size must come from a reliable venue rule and may
not be inferred by optimising test results. The checked-in config therefore fails
while tick size remains null.

## Source, licensing, and data contract

The official provider pages confirm a 2012-06-21 AAPL depth-10 sample, a six-column
message file, and a 4×levels orderbook file. Message row k corresponds positionally
to post-event orderbook row k. Timestamps are not unique keys; `event_index` is the
stable raw-row key and `research_index` is the position among eligible rows.

Prices use an integer scale of 10,000. Empty levels use documented sentinel prices
and zero volume. Event types 1–7 include submissions, cancellations, deletions,
visible/hidden executions, cross trades, and halt indicators. Current sample terms
restrict redistribution, so raw and derived local datasets are gitignored.

## Quality pipeline

The ingest stage preserves raw order and rejects unequal file lengths or malformed
fields. Validation records a reason per invalid row, rather than silently dropping
it. Current policy can exclude locked/crossed books, nonpositive prices, negative
sizes, decreasing time, and halt messages. Reports retain raw, eligible, excluded,
reason, and time-boundary counts. JSON and Parquet outputs use temporary files and
atomic rename so interrupted writes do not masquerade as successful artifacts.

Synthetic tests cover duplicate timestamps, upward/downward quote moves, zero
volume, locked/crossed books, row-count mismatch, and invalid source metadata.
These tests establish behavior, not empirical market-data quality.

## Feature definitions and causal timing

Every feature describes the post-event book at t and reads no event after t.
Midprice is `(bid1 + ask1)/2`; spread is `ask1-bid1`; relative spread divides by
Midprice. OBI is weighted bid minus ask depth divided by total depth, with equal
weights for L1/L5/L10. A zero denominator produces null.

Microprice cross-weights each best quote by opposite-side size. For valid positive
quotes it must lie inside the best bid/ask interval. Microprice deviation is its
relative difference from Midprice.

Event OFI implements all four quote-change terms for best bid and ask. Rolling OFI
uses the last 10, 20, or 50 complete OFI events along the eligible sequence. The
first event and incomplete warmup windows remain null. `raw_gap_events` discloses
when adjacent research events skipped invalid raw rows.

Python vectorised, native Python-loop, and C++17 implementations share the same
event convention. An 80-row depth-10 synthetic fixture passed 12-feature numeric
and null-mask parity at `abs(a-b) <= 1e-9 + 1e-8*abs(b)`.

## Labels and leakage control

For each horizon, the label uses `log(mid[t+h]/mid[t])`. It is +1 above the positive
threshold, -1 below the negative threshold, and 0 inside it. Tail rows without a
future observation remain null, and each label stores its end event/research index.

Chronological boundaries approximate 60/20/20 Train/Validation/Test. A sample is
purged when its label window crosses the next boundary. Preprocessing fits median
imputation and scaling on Train only. OBI threshold and XGBoost hyperparameters use
Validation only. Test is reserved for one frozen evaluation.

## Models and evaluation protocol

M0 predicts the Train majority class. M1 is a symmetric OBI threshold rule. M2 is
median imputation, standardisation, and multinomial Logistic Regression. M3 is a
fixed-seed, single-thread XGBoost classifier chosen by Validation log loss. Training
fails if Train does not contain all three classes rather than hiding the deficiency.

Frozen models must predict identical Test event IDs. Reported metrics are Macro-F1,
Balanced Accuracy, MCC, per-class precision/recall/support, Log Loss, multiclass
Brier score, and a fixed-order confusion matrix. Time and spread slices are
descriptive; highly autocorrelated event rows are not treated as independent
observations and no naïve i.i.d. p-value is reported.

## Single-day empirical results

On the frozen Test segments, XGBoost Macro-F1 was 0.3903, 0.3603, and 0.3942 for
h10/h20/h50. Corresponding MCC was 0.1007, 0.1820, and 0.2206. These descriptive
single-day results exceed the majority Macro-F1 values of 0.2141, 0.1972, and
0.2206, but they are not evidence of out-of-day alpha. Complete class metrics, Log
Loss, Brier scores, and confusion matrices are stored in the ignored run artifacts.

## Trading-cost sensitivity

The scenario generator crosses half/full spread, multiple fee assumptions, and
0/1/5-event delays. It is a sensitivity table only. There is no fill probability,
queue position, market impact, or calibrated execution-price model. It therefore
cannot support a net-profit claim.

## C++ parity and performance methodology

The C++17 Release CLI reads canonical CSV and writes fixed-order feature CSV.
Malformed inputs return an error, and existing outputs require `--force`. CTest
covers build, CSV, L1, OFI, depth/rolling, and CLI behavior.

A fair benchmark separates parse, compute, and write time; warms each implementation;
stores at least five raw repetitions; and reports median, range/IQR, throughput,
peak-memory method, OS, CPU, compiler, flags, versions, threads, and input hash.
Runs are incomparable if hashes, Release mode, or single-thread conditions differ.
No minimum C++ speedup is assumed. On this environment the median C++ total was
2.6190 seconds (about 152,880 records/s), native Python-loop compute was 5.8386
seconds, and vectorised Pandas/NumPy compute was 0.1831 seconds (about 2.19 million
records/s). C++ beat the native loop but was materially slower than vectorisation;
the report therefore makes no blanket C++ performance claim.

## Failure cases and limitations

Important failure cases include malformed positional alignment, zero depth, quote
sentinels, halts, long invalid gaps, absent label classes, and model calibration
under class imbalance. Even a technically correct single-day split may reflect
intraday regime persistence and overlapping information rather than a stable law.

The study lacks multiple days, queue reconstruction, L3 order priority, fill
probabilities, market impact, and live latency engineering. Exact filenames, hashes,
row count, session, and the Rule-612 tick source are recorded. The remaining design
constraints prevent statements about cross-day alpha, capacity, or deployable
profitability.

## Reproduction status and next evidence

The repository's synthetic unit tests, Python/C++ CTests, parity test, lint, and
format checks are executable in CI without restricted data. The empirical run
`lobster_aapl_20120621_l10_v2` is frozen locally with provenance, models,
predictions, metrics, slices, costs, benchmark repetitions, and artifact hashes. A
later multi-day extension should use anchored walk-forward splits by day and preserve
this single-day run as an immutable record.

