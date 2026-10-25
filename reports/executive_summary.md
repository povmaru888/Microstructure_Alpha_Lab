# Microstructure Alpha Lab — Executive Summary

## Question

Can contemporaneous order-book imbalance, quote-change order-flow imbalance, and
Microprice deviation help classify Midprice direction 10, 20, or 50 eligible book
updates ahead?

## Data and integrity boundary

The input is the official LOBSTER AAPL 2012-06-21 depth-10 sample, downloaded after
the user confirmed the sample terms. Its 400,391 aligned rows cover 09:30–16:00;
raw data remains local and gitignored. Provider format, event codes, price scale,
sentinels, alignment, hashes, session, Rule-612 tick source, and redistribution
constraints are documented. This remains a single-day study with no profit or
cross-day alpha claim.

## Method

The pipeline preserves raw row order, creates stable `event_index` and filtered
`research_index` keys, records exclusion reasons, and writes provenance-hashed
atomic artifacts. Causal features include Midprice/spread, equal-weight OBI at
L1/L5/L10, Microprice/deviation, Event OFI, and rolling OFI at 10/20/50 events.

Labels use future event-time Midprice only in the target. Chronological 60/20/20
splits purge label windows that cross boundaries. Imputation/scaling fit on Train;
OBI and XGBoost selection use Validation; Test remains frozen. Models are majority,
OBI rule, Logistic Regression, and XGBoost. Evaluation fixes common Test IDs and
reports Macro-F1, balanced accuracy, MCC, class metrics, Log Loss, Brier score,
confusion matrices, and descriptive time/spread slices.

## Verified findings

- Synthetic edge cases verify duplicate timestamps, bad alignment, invalid books,
  null denominators, label tails, purge boundaries, and train-only preprocessing.
- Python vectorised, native-loop, and C++17 formulas agree on the canonical fixture;
  Python/C++ parity passed for 80 rows × 12 features including null masks.
- C++ Release builds and six CTests pass. CI requires ruff, pytest, CTest, and parity.
- Benchmark machinery stores at least five raw samples and refuses comparisons with
  mismatched hashes, non-Release builds, or multiple threads.

The frozen AAPL run produced XGBoost Macro-F1 of 0.3903/0.3603/0.3942 for
h10/h20/h50, versus majority 0.2141/0.1972/0.2206. C++ processed about 152,880
records/s, faster than the native loop but much slower than vectorised compute at
about 2.19 million records/s. These are environment- and single-day-specific facts,
not general alpha or C++ superiority claims.

## Failure cases and limitations

The design fails fast on missing tick size, corrupt row alignment, unavailable
classes, duplicate run IDs, malformed C++ input, parity mismatch, and output
overwrite. It does not model L3 queues, fill probability, market impact, or live
latency. Cost scenarios are sensitivity analysis only, not net-profit estimates.
Single-day event samples are autocorrelated and cannot demonstrate cross-day
generalisability.

## Three-minute takeaway

The deliverable is a correctness-first research platform, not a performance claim:
data provenance and leakage controls are explicit, Python is the reference, C++ is
numerically checked against it, and every empirical claim requires a frozen,
traceable run. The next legitimate step is a lawful AAPL sample run followed by a
separately versioned multi-day anchored walk-forward study.

