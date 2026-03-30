from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.signal import butter, filtfilt

from .paths import (
    default_output_dir,
    displacement_filename,
    is_aligned_acceleration_file,
)

CUTOFF_FREQUENCY_HZ = 0.5
FILTER_ORDER = 6


def load_processed_acceleration_data(file_path: Path) -> np.ndarray:
    rows: list[list[float]] = []
    with file_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue

            parts = stripped.split()
            if len(parts) != 4:
                continue

            try:
                rows.append([float(value) for value in parts])
            except ValueError:
                continue

    if not rows:
        raise ValueError(f"No numeric data found in {file_path}")

    data = np.asarray(rows, dtype=float)
    if data.shape[1] != 4:
        raise ValueError(f"Expected 4 columns in {file_path}, found {data.shape[1]}")
    return data


def compute_sample_rate(time_values: np.ndarray) -> float:
    time_deltas = np.diff(np.asarray(time_values, dtype=float))
    positive_deltas = time_deltas[time_deltas > 0.0]
    if len(positive_deltas) == 0:
        raise ValueError("Cannot compute sample rate from time column with non-increasing values.")

    dt = float(np.median(positive_deltas))
    if dt <= 0.0:
        raise ValueError("Computed invalid sample interval from time column.")
    return 1.0 / dt


def high_pass_filter(
    signal: np.ndarray,
    cutoff_hz: float,
    sample_rate: float,
    order: int = FILTER_ORDER,
) -> np.ndarray:
    nyquist = sample_rate / 2.0
    if not 0.0 < cutoff_hz < nyquist:
        raise ValueError(
            f"High-pass cutoff must be between 0 and Nyquist frequency ({nyquist:.6f} Hz)."
        )
    b, a = butter(order, cutoff_hz / nyquist, btype="highpass")
    return filtfilt(b, a, np.asarray(signal, dtype=float))


def acceleration_to_displacement(
    acceleration: np.ndarray,
    sampling_frequency: float,
) -> np.ndarray:
    filtered_acc = high_pass_filter(acceleration, CUTOFF_FREQUENCY_HZ, sampling_frequency)
    dt = 1.0 / sampling_frequency
    speed = np.cumsum(filtered_acc) * dt
    filtered_speed = high_pass_filter(speed, CUTOFF_FREQUENCY_HZ, sampling_frequency)
    displacement = np.cumsum(filtered_speed) * dt
    displacement_mm = displacement * 1000.0
    return high_pass_filter(displacement_mm, CUTOFF_FREQUENCY_HZ, sampling_frequency)


def convert_acceleration_data_to_displacement(data: np.ndarray) -> np.ndarray:
    time_values = data[:, 0]
    sampling_frequency = compute_sample_rate(time_values)
    displacement_xyz = np.column_stack(
        [
            acceleration_to_displacement(data[:, column_index], sampling_frequency)
            for column_index in range(1, 4)
        ]
    )
    return np.column_stack((time_values, displacement_xyz))


def save_displacement_data(data: np.ndarray, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        handle.write("time\tdisp_x\tdisp_y\tdisp_z\n")
        for row in data:
            handle.write(f"{row[0]:.6f}\t{row[1]:.6f}\t{row[2]:.6f}\t{row[3]:.6f}\n")


def process_displacement_data(
    input_dir: Path | None = None,
    output_dir: Path | None = None,
) -> int:
    input_dir = input_dir or default_output_dir()
    output_dir = output_dir or default_output_dir()

    input_files = sorted(file_path for file_path in input_dir.glob("*.txt") if is_aligned_acceleration_file(file_path))
    if not input_files:
        raise FileNotFoundError(f"No aligned acceleration .txt files found in {input_dir}")

    print(f"Processing {len(input_files)} processed acceleration file(s) from: {input_dir}")

    for input_file in input_files:
        print(f"Converting {input_file.name} to displacement")
        acceleration_data = load_processed_acceleration_data(input_file)
        displacement_data = convert_acceleration_data_to_displacement(acceleration_data)

        output_file = output_dir / displacement_filename(input_file)
        save_displacement_data(displacement_data, output_file)
        print(f"Saved displacement data: {output_file}")

    return 0
