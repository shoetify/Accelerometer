from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

from .paths import default_calibration_path, default_input_dir

GRAVITY = 9.80665


@dataclass(frozen=True)
class TimeWindow:
    label: str
    start_time: float
    end_time: float


@dataclass(frozen=True)
class CalibrationPoint:
    label: str
    source_file: str
    window: TimeWindow
    mean_xyz: np.ndarray
    sample_count: int


@dataclass(frozen=True)
class CalibrationResult:
    gravity: float
    scales: np.ndarray
    offsets: np.ndarray
    calibration_points: list[CalibrationPoint]
    corrected_norms: np.ndarray


def load_data(file_path: Path) -> np.ndarray:
    rows: list[list[float]] = []
    data_section_started = False
    with file_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not data_section_started:
                if stripped.startswith("---"):
                    data_section_started = True
                continue

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

    return np.asarray(rows, dtype=float)


def prompt_window(file_path: Path, test_label: str, min_time: float, max_time: float) -> TimeWindow:
    while True:
        raw = input(
            f"{file_path.name} {test_label} "
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
        return TimeWindow(label=test_label, start_time=start_time, end_time=end_time)


def compute_mean_xyz(data: np.ndarray, window: TimeWindow) -> tuple[np.ndarray, int]:
    mask = (data[:, 0] >= window.start_time) & (data[:, 0] <= window.end_time)
    windowed = data[mask]
    if len(windowed) == 0:
        raise ValueError(
            f"No samples found in range {window.start_time} to {window.end_time} for {window.label}"
        )
    return windowed[:, 1:4].mean(axis=0), len(windowed)


def fit_calibration(points: np.ndarray) -> np.ndarray:
    x0 = np.array([30.0, 30.0, 30.0, 1.75, 1.75, 1.75], dtype=float)
    lower_bounds = np.array([25.0, 25.0, 25.0, 1.5, 1.5, 1.5], dtype=float)
    upper_bounds = np.array([35.0, 35.0, 35.0, 2.0, 2.0, 2.0], dtype=float)

    def residuals(params: np.ndarray) -> np.ndarray:
        scales = params[:3]
        offsets = params[3:]
        transformed = (points - offsets) * scales
        return np.sum(transformed**2, axis=1) - GRAVITY**2

    result = least_squares(
        residuals,
        x0=x0,
        bounds=(lower_bounds, upper_bounds),
        method="trf",
        ftol=1e-12,
        xtol=1e-12,
        gtol=1e-12,
        max_nfev=100000,
    )

    if not result.success:
        raise RuntimeError(f"Calibration fit failed: {result.message}")

    return result.x


def format_point(point: CalibrationPoint) -> str:
    x_value, y_value, z_value = point.mean_xyz
    return (
        f"{point.label}: x={x_value:.6f}, y={y_value:.6f}, z={z_value:.6f} "
        f"[{point.source_file}, {point.window.start_time:.3f}-{point.window.end_time:.3f}, "
        f"samples={point.sample_count}]"
    )


def save_calibration_result(result: CalibrationResult, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "gravity": result.gravity,
        "parameters": {
            "a1": float(result.scales[0]),
            "a2": float(result.scales[1]),
            "a3": float(result.scales[2]),
            "b1": float(result.offsets[0]),
            "b2": float(result.offsets[1]),
            "b3": float(result.offsets[2]),
        },
        "calibration_points": [
            {
                "label": point.label,
                "source_file": point.source_file,
                "time_window": {
                    "label": point.window.label,
                    "start_time": point.window.start_time,
                    "end_time": point.window.end_time,
                },
                "mean_xyz": {
                    "x": float(point.mean_xyz[0]),
                    "y": float(point.mean_xyz[1]),
                    "z": float(point.mean_xyz[2]),
                },
                "sample_count": point.sample_count,
                "corrected_norm": float(result.corrected_norms[index]),
            }
            for index, point in enumerate(result.calibration_points)
        ],
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_calibration_result(input_path: Path) -> CalibrationResult:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    calibration_points = [
        CalibrationPoint(
            label=item["label"],
            source_file=item["source_file"],
            window=TimeWindow(
                label=item["time_window"]["label"],
                start_time=float(item["time_window"]["start_time"]),
                end_time=float(item["time_window"]["end_time"]),
            ),
            mean_xyz=np.array(
                [
                    float(item["mean_xyz"]["x"]),
                    float(item["mean_xyz"]["y"]),
                    float(item["mean_xyz"]["z"]),
                ],
                dtype=float,
            ),
            sample_count=int(item["sample_count"]),
        )
        for item in payload["calibration_points"]
    ]
    return CalibrationResult(
        gravity=float(payload["gravity"]),
        scales=np.array(
            [
                float(payload["parameters"]["a1"]),
                float(payload["parameters"]["a2"]),
                float(payload["parameters"]["a3"]),
            ],
            dtype=float,
        ),
        offsets=np.array(
            [
                float(payload["parameters"]["b1"]),
                float(payload["parameters"]["b2"]),
                float(payload["parameters"]["b3"]),
            ],
            dtype=float,
        ),
        calibration_points=calibration_points,
        corrected_norms=np.array(
            [float(item["corrected_norm"]) for item in payload["calibration_points"]],
            dtype=float,
        ),
    )


def run_calibration(
    input_dir: Path | None = None,
    output_path: Path | None = None,
) -> int:
    input_dir = input_dir or default_input_dir()
    files = sorted(input_dir.glob("*.txt"))
    if len(files) != 3:
        raise FileNotFoundError(f"Expected 3 .txt files in {input_dir}, found {len(files)}")

    print("Accelerometer calibration")
    print(f"Using input folder: {input_dir}")
    print()

    calibration_points: list[CalibrationPoint] = []
    point_index = 1

    for file_path in files:
        data = load_data(file_path)
        min_time = float(data[:, 0].min())
        max_time = float(data[:, 0].max())
        print(f"{file_path.name}: {len(data)} rows, time {min_time:.3f} to {max_time:.3f}")

        for test_number in range(1, 3):
            window = prompt_window(file_path, f"test_{test_number}", min_time, max_time)
            mean_xyz, sample_count = compute_mean_xyz(data, window)
            calibration_points.append(
                CalibrationPoint(
                    label=f"group_{point_index}",
                    source_file=file_path.name,
                    window=window,
                    mean_xyz=mean_xyz,
                    sample_count=sample_count,
                )
            )
            point_index += 1

        print()

    points = np.asarray([point.mean_xyz for point in calibration_points], dtype=float)
    params = fit_calibration(points)
    scales = params[:3]
    offsets = params[3:]
    corrected = (points - offsets) * scales
    corrected_norms = np.linalg.norm(corrected, axis=1)
    result = CalibrationResult(
        gravity=GRAVITY,
        scales=scales,
        offsets=offsets,
        calibration_points=calibration_points,
        corrected_norms=corrected_norms,
    )

    print("Averaged calibration points")
    for point in calibration_points:
        print(format_point(point))

    print()
    print("Calibration parameters")
    print(f"a1={scales[0]:.10f}")
    print(f"a2={scales[1]:.10f}")
    print(f"a3={scales[2]:.10f}")
    print(f"b1={offsets[0]:.10f}")
    print(f"b2={offsets[1]:.10f}")
    print(f"b3={offsets[2]:.10f}")

    print()
    print("Residual check")
    for index, norm_value in enumerate(corrected_norms, start=1):
        print(f"group_{index}: corrected_norm={norm_value:.10f}, target={GRAVITY:.10f}")

    output_path = output_path or default_calibration_path()
    save_calibration_result(result, output_path)

    print()
    print(f"Saved calibration result to: {output_path}")

    return 0
