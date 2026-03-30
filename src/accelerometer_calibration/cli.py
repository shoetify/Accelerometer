from __future__ import annotations

import argparse
from pathlib import Path

from .calibration import run_calibration
from .processing import process_experiment_data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Accelerometer calibration and data analysis tools.")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("calibrate", help="Run the interactive calibration workflow.")

    process_parser = subparsers.add_parser(
        "process",
        help="Apply saved calibration parameters to all experiment files in input/.",
    )
    process_parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path.cwd() / "input",
        help="Directory containing experiment .txt files.",
    )
    process_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd() / "output",
        help="Directory for processed output files.",
    )
    process_parser.add_argument(
        "--calibration",
        type=Path,
        default=Path.cwd() / "output" / "calibration_result.json",
        help="Path to calibration_result.json.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command in (None, "calibrate"):
        return run_calibration()
    if args.command == "process":
        return process_experiment_data(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            calibration_path=args.calibration,
        )

    parser.error(f"Unknown command: {args.command}")
    return 2
