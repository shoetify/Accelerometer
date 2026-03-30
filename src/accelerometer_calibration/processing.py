from __future__ import annotations

from pathlib import Path

import numpy as np

from .calibration import load_calibration_result, load_data
from .paths import (
    aligned_acceleration_filename,
    default_output_dir,
    default_input_dir,
    resolve_calibration_path,
)


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


def prompt_stable_window(file_path: Path, min_time: float, max_time: float) -> tuple[float, float]:
    while True:
        raw = input(
            f"{file_path.name} stable range "
            f"(time range {min_time:.3f} to {max_time:.3f}) "
            f"enter start_time,end_time: "
        ).strip()
        try:
            start_text, end_text = [part.strip() for part in raw.split(",", maxsplit=1)]
            start_time = float(start_text)
            end_time = float(end_text)
        except ValueError:
            print("Invalid input. Enter two numbers separated by a comma.")
            continue

        if start_time >= end_time:
            print("Invalid window. start_time must be smaller than end_time.")
            continue
        if start_time < min_time or end_time > max_time:
            print("Window outside file time range.")
            continue
        return start_time, end_time


def compute_average_xyz(data: np.ndarray, start_time: float, end_time: float) -> np.ndarray:
    mask = (data[:, 0] >= start_time) & (data[:, 0] <= end_time)
    windowed = data[mask]
    if len(windowed) == 0:
        raise ValueError(f"No samples found in range {start_time} to {end_time}")
    return windowed[:, 1:4].mean(axis=0)


def compute_rotation_matrix(source_vector: np.ndarray, target_vector: np.ndarray) -> np.ndarray:
    source_norm = np.linalg.norm(source_vector)
    target_norm = np.linalg.norm(target_vector)
    if source_norm == 0.0 or target_norm == 0.0:
        raise ValueError("Rotation cannot be computed from a zero-length vector.")

    source_unit = source_vector / source_norm
    target_unit = target_vector / target_norm
    cross = np.cross(source_unit, target_unit)
    sin_theta = np.linalg.norm(cross)
    cos_theta = float(np.clip(np.dot(source_unit, target_unit), -1.0, 1.0))

    if sin_theta < 1e-12:
        if cos_theta > 0.0:
            return np.eye(3)

        reference = np.array([1.0, 0.0, 0.0], dtype=float)
        if abs(source_unit[0]) > 0.9:
            reference = np.array([0.0, 0.0, 1.0], dtype=float)
        axis = np.cross(source_unit, reference)
        axis = axis / np.linalg.norm(axis)
        return -np.eye(3) + 2.0 * np.outer(axis, axis)

    axis = cross / sin_theta
    skew = np.array(
        [
            [0.0, -axis[2], axis[1]],
            [axis[2], 0.0, -axis[0]],
            [-axis[1], axis[0], 0.0],
        ],
        dtype=float,
    )
    return np.eye(3) + skew * sin_theta + (skew @ skew) * (1.0 - cos_theta)


def rotate_processed_data(data: np.ndarray, rotation_matrix: np.ndarray) -> np.ndarray:
    rotated_xyz = data[:, 1:4] @ rotation_matrix.T
    return np.column_stack((data[:, 0], rotated_xyz))


def process_experiment_data(
    input_dir: Path | None = None,
    output_dir: Path | None = None,
    calibration_path: Path | None = None,
) -> int:
    input_dir = input_dir or default_input_dir()
    output_dir = output_dir or default_output_dir()
    calibration_path = resolve_calibration_path(calibration_path, output_dir)

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
        min_time = float(processed_data[:, 0].min())
        max_time = float(processed_data[:, 0].max())
        start_time, end_time = prompt_stable_window(input_file, min_time, max_time)
        average_xyz = compute_average_xyz(processed_data, start_time, end_time)
        target_gravity = np.array([0.0, calibration.gravity, 0.0], dtype=float)
        rotation_matrix = compute_rotation_matrix(average_xyz, target_gravity)
        rotated_data = rotate_processed_data(processed_data, rotation_matrix)

        print(
            f"{input_file.name} stable-window mean: "
            f"x0={average_xyz[0]:.6f}, y0={average_xyz[1]:.6f}, z0={average_xyz[2]:.6f}"
        )
        print(f"{input_file.name} rotation matrix:")
        for row in rotation_matrix:
            print(f"  {row[0]: .10f} {row[1]: .10f} {row[2]: .10f}")

        output_file = output_dir / aligned_acceleration_filename(input_file)
        save_processed_data(rotated_data, output_file)
        print(f"Saved processed data: {output_file}")

    return 0
