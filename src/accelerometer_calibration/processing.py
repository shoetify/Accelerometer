from __future__ import annotations

from pathlib import Path

import numpy as np

from .calibration import load_calibration_result, load_data


def apply_calibration_parameters(
    data: np.ndarray,
    scales: np.ndarray,
    offsets: np.ndarray,
) -> np.ndarray:
    corrected_xyz = (data[:, 1:4] - offsets) * scales
    return np.column_stack((data[:, 0], corrected_xyz))


def save_processed_data(data: np.ndarray, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        handle.write("time\tX\tY\tZ\n")
        for row in data:
            handle.write(f"{row[0]:.6f}\t{row[1]:.6f}\t{row[2]:.6f}\t{row[3]:.6f}\n")


def process_experiment_data(
    input_dir: Path | None = None,
    output_dir: Path | None = None,
    calibration_path: Path | None = None,
) -> int:
    base_dir = Path.cwd()
    input_dir = input_dir or (base_dir / "input")
    output_dir = output_dir or (base_dir / "output")
    calibration_path = calibration_path or (output_dir / "calibration_result.json")

    calibration = load_calibration_result(calibration_path)
    print(f"Loaded calibration result from: {calibration_path}")
    print(f"Gravity={calibration.gravity:.6f}")
    print(
        "Parameters: "
        f"a1={calibration.scales[0]:.10f}, "
        f"a2={calibration.scales[1]:.10f}, "
        f"a3={calibration.scales[2]:.10f}, "
        f"b1={calibration.offsets[0]:.10f}, "
        f"b2={calibration.offsets[1]:.10f}, "
        f"b3={calibration.offsets[2]:.10f}"
    )

    input_files = sorted(input_dir.glob("*.txt"))
    if not input_files:
        raise FileNotFoundError(f"No .txt files found in {input_dir}")

    print(f"Processing {len(input_files)} experiment file(s) from: {input_dir}")

    for input_file in input_files:
        raw_data = load_data(input_file)
        processed_data = apply_calibration_parameters(
            raw_data,
            calibration.scales,
            calibration.offsets,
        )
        output_file = output_dir / f"{input_file.stem}_processed.txt"
        save_processed_data(processed_data, output_file)
        print(f"Saved processed data: {output_file}")

    return 0
