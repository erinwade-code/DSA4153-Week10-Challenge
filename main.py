"""Entry point: python main.py --config config.json"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from src.pipeline import ValidationReport, run_pipeline, write_failure_report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the command line."""
    parser = argparse.ArgumentParser(description="Four-format data recovery and validation")
    parser.add_argument("--config", required=True, help="path to config.json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the pipeline; return 0 on success and 1 on any failure."""
    args = parse_args(argv)
    report, cfg, error, ok = ValidationReport(), {}, None, False
    try:
        cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
        ok = run_pipeline(cfg, report)
    except Exception as exc:  # file/schema errors and conflicting keys stop the run
        error = exc
        print(f"FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
    if ok:
        print(f"SUCCESS: {len(report.rows)} checks passed. "
              f"Outputs published to {cfg.get('output_dir', 'outputs')}/")
        return 0
    for row in report.failures():
        print(f"  failed check: {row['check']} (expected {row['expected']}, "
              f"actual {row['actual']})", file=sys.stderr)
    shutil.rmtree(cfg.get("staging_dir", "staging"), ignore_errors=True)
    path = write_failure_report(cfg.get("output_dir", "outputs"), report, error)
    print(f"Failed validation report saved to {path}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())