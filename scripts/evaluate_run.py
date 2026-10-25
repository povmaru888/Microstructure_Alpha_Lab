#!/usr/bin/env python3
"""Evaluate frozen models and write fixed Test artifacts."""

import argparse
from pathlib import Path

from microalpha.evaluate import evaluate_run


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--features", type=Path, required=True)
    args = parser.parse_args()
    evaluate_run(args.run_dir, args.features)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
