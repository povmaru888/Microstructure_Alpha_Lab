# Release checklist

- [x] Synthetic-only tests; no licensed raw fixture committed.
- [x] `.gitignore` excludes raw, processed, artifacts, environments, and secrets.
- [x] Python 3.12 lint, format, pytest, C++17 Release, CTest, and parity are in CI.
- [x] Ubuntu 24.04 and Windows build runners are configured.
- [x] Research report and dashboard state single-day/non-live limitations.
- [x] Missing empirical measurements remain null.
- [x] Lawfully downloaded LOBSTER raw smoke: 400,391 aligned rows, hashes/session
  recorded, features/models/evaluation/benchmark completed locally after explicit
  user confirmation of the current sample terms.

Before publishing, inspect the exact Git index with `git ls-files`, run the full
commands in README, review provider terms again, and attach the CI run URLs.

