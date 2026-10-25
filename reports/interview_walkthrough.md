# Interview Walkthrough

## 0:00–0:30 — Frame the question

“I built a correctness-first microstructure research lab to test whether OBI, quote
OFI, and Microprice help classify Midprice direction in event time. It is explicitly
not a live HFT system and I do not claim profit or cross-day alpha.”

Show the README scope and the permanent dashboard warning.

## 0:30–1:30 — Data provenance and failure behavior

Open `docs/source_verification.md`, `configs/experiment.yaml`, and the manifest code.
Explain positional message/orderbook alignment, stable `event_index`, filtered
`research_index`, SHA-256, row counts, event codes, sentinels, and atomic outputs.

Demonstrate two deliberate failures: null tick size blocks half-tick labels; unequal
CSV lengths block ingest. Emphasise that licensed raw is ignored and was not used by
CI. The exact AAPL raw remains local and is never redistributed.

## 1:30–3:00 — Hypothesis and causal research design

Walk through Midprice/spread, L1/L5/L10 OBI, Microprice/deviation, four-term Event
OFI, and W10/W20/W50 rolling OFI. Show tests for hand calculations, zero denominators,
warmup nulls, and future-change invariance.

Explain labels at h=10/20/50, half-tick threshold, chronological 60/20/20 split, and
purging any label window that crosses a boundary. Train-only preprocessing and
Validation-only OBI/XGBoost selection keep Test frozen.

## 3:00–4:00 — Model and evaluation contract

Compare majority, OBI rule, Logistic Regression, and fixed-seed XGBoost, LightGBM,
and CatBoost on identical
Test event IDs. Metrics include Macro-F1, balanced accuracy, MCC, per-class metrics,
Log Loss, Brier score, and confusion matrices. Time/spread slices are descriptive;
there are no naïve i.i.d. significance claims for autocorrelated events.

State clearly that the AAPL scores are single-day descriptive results, supported by
synthetic correctness tests, and are not cross-day or tradable-alpha evidence.

## 4:00–5:00 — Python/C++ parity

Build the C++17 Release CLI and run CTest. Show that the same canonical depth-10 CSV
is processed by Python and C++, joined on dataset/event key, compared across 12
features, and checked for identical null masks. The current synthetic parity case
covers 80 rows and uses a fixed absolute/relative tolerance.

## 5:00–6:00 — Performance without benchmark theatre

Explain separate parse/compute/write stages, warmup, at least five raw repetitions,
median/range/IQR, throughput, RSS method, Release mode, input hash, and one-thread
comparability. No speedup is promised; missing C++ measurement remains null.

## 6:00–7:00 — Limitations and next experiment

- Single day cannot demonstrate cross-day generalisation.
- No broker connection, live order gateway, L3 matching, queue priority, fill model,
  calibrated impact, or production low-latency engineering.
- Cost scenarios are sensitivity analysis, not executable P&L.
- The next legitimate evidence is a frozen lawful AAPL run, followed by a separately
  versioned multi-day anchored walk-forward study.

Close with: “The portfolio claim is reproducible research engineering and numerical
parity. Any alpha claim must wait for licensed data and out-of-day evidence.”

## Demo commands

```bash
.venv/bin/ruff check .
.venv/bin/pytest -q
.venv/bin/cmake -S cpp -B cpp/build -DCMAKE_BUILD_TYPE=Release
.venv/bin/cmake --build cpp/build --config Release
.venv/bin/ctest --test-dir cpp/build --output-on-failure -C Release
```

