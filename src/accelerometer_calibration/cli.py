from __future__ import annotations

import argparse
from pathlib import Path

from .calibration import run_calibration
from .displacement import process_displacement_data
from .paths import default_calibration_path, default_input_dir, default_output_dir
from .processing import process_experiment_data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="accelerometer",
        description="Calibrate accelerometer data, process experiments, and derive displacement files.",
        epilog=(
            "Examples:\n"
            "  accelerometer\n"
            "  accelerometer process\n"
            "  accelerometer displacement --input-dir output"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    calibrate_parser = subparsers.add_parser(
        "calibrate",
        help="Run the interactive calibration workflow.",
    )
    calibrate_parser.add_argument(
        "--input-dir",
        type=Path,
        default=default_input_dir(),
        help="Directory containing the 3 calibration .txt files.",
    )
    calibrate_parser.add_argument(
        "--output",
        type=Path,
        default=default_calibration_path(),
        help="Path for the saved calibration JSON file.",
    )

    process_parser = subparsers.add_parser(
        "process",
        help="Apply saved calibration parameters to all experiment files in input/.",
    )
    process_parser.add_argument(
        "--input-dir",
        type=Path,
        default=default_input_dir(),
        help="Directory containing experiment .txt files.",
    )
    process_parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_output_dir(),
        help="Directory for processed output files.",
    )
    process_parser.add_argument(
        "--calibration",
        type=Path,
        default=default_calibration_path(),
        help="Path to calibration.json.",
    )

    displacement_parser = subparsers.add_parser(
        "displacement",
        help="Convert aligned acceleration files in output/ to displacement data in output/.",
    )
    displacement_parser.add_argument(
        "--input-dir",
        type=Path,
        default=default_output_dir(),
        help="Directory containing aligned acceleration files.",
    )
    displacement_parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_output_dir(),
        help="Directory for displacement output files.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command in (None, "calibrate"):
        return run_calibration(
            input_dir=args.input_dir if args.command == "calibrate" else None,
            output_path=args.output if args.command == "calibrate" else None,
        )
    if args.command == "process":
        return process_experiment_data(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            calibration_path=args.calibration,
        )
    if args.command == "displacement":
        return process_displacement_data(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
        )

    parser.error(f"Unknown command: {args.command}")
    return 2
