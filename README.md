# Microstructure Alpha Lab

Reproducible, CPU-only market-microstructure research pipeline for OBI, quote
change OFI, Microprice, event-time direction labels, baseline models, Python/C++
parity, and fair performance measurement.

This is a research portfolio project, not a live trading system. A single-day
LOBSTER sample cannot establish cross-day generalisation or tradable profit.

## Environment

Requires Python 3.12, a C++17 compiler, and CMake. Create an isolated environment:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip install --no-deps -e .
```

On Windows use `.venv\Scripts\python` and `.venv\Scripts\pip`.

## Licensed data

Review the provider's current terms and obtain the AAPL 2012-06-21 depth-10
sample lawfully. Do not commit or redistribute its archive or CSV files. Follow
[data/README.md](data/README.md) and record the actual filenames, source URL,
download time, SHA-256, row counts, session, and independently verified tick rule.

The checked-in `configs/experiment.yaml` deliberately leaves `tick_size: null`.
Make a run-specific copy and set it only after verification.

## Pipeline

```bash
.venv/bin/python scripts/prepare_data.py \
  --config configs/experiment.local.yaml \
  --source-page https://php.lobsterdata.com/info/DataSamples.php \
  --license-note "Reviewed provider terms" \
  --output-dir artifacts/data

.venv/bin/python scripts/run_experiment.py \
  --config configs/experiment.local.yaml \
  --features artifacts/data/features.parquet \
  --run-id aapl_day1_v1 \
  --output-dir artifacts

.venv/bin/python scripts/run_benchmark.py \
  --input artifacts/data/validated.parquet \
  --run-id aapl_day1_v1 \
  --output-dir artifacts

.venv/bin/python scripts/evaluate_run.py \
  --run-dir artifacts/aapl_day1_v1 \
  --features artifacts/data/features.parquet

.venv/bin/python -m streamlit run app/dashboard.py
```

## C++ and verification

```bash
.venv/bin/cmake -S cpp -B cpp/build -DCMAKE_BUILD_TYPE=Release
.venv/bin/cmake --build cpp/build --config Release
.venv/bin/ctest --test-dir cpp/build --output-on-failure -C Release
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pytest -q
```

All repository tests use tiny synthetic fixtures. No restricted raw data is
required by CI. Benchmark results must include raw repetitions and parity evidence;
missing measurements stay null and no minimum C++ speedup is promised.

