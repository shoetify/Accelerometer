from __future__ import annotations

from pathlib import Path


INPUT_DIRNAME = "input"
OUTPUT_DIRNAME = "output"

CALIBRATION_FILENAME = "calibration.json"
LEGACY_CALIBRATION_FILENAME = "calibration_result.json"

ALIGNED_ACCELERATION_SUFFIX = "_aligned_acceleration.txt"
LEGACY_PROCESSED_SUFFIX = "_processed.txt"

DISPLACEMENT_SUFFIX = "_displacement_mm.txt"
LEGACY_DISPLACEMENT_SUFFIX = "_displacement.txt"


def project_path(*parts: str) -> Path:
    return Path.cwd().joinpath(*parts)


def default_input_dir() -> Path:
    return project_path(INPUT_DIRNAME)


def default_output_dir() -> Path:
    return project_path(OUTPUT_DIRNAME)


def default_calibration_path(output_dir: Path | None = None) -> Path:
    base_output_dir = output_dir or default_output_dir()
    return base_output_dir / CALIBRATION_FILENAME


def resolve_calibration_path(path: Path | None = None, output_dir: Path | None = None) -> Path:
    if path is not None:
        return path

    base_output_dir = output_dir or default_output_dir()
    default_path = base_output_dir / CALIBRATION_FILENAME
    legacy_path = base_output_dir / LEGACY_CALIBRATION_FILENAME

    if default_path.exists() or not legacy_path.exists():
        return default_path
    return legacy_path


def aligned_acceleration_filename(source_file: Path) -> str:
    return f"{source_file.stem}{ALIGNED_ACCELERATION_SUFFIX}"


def is_aligned_acceleration_file(file_path: Path) -> bool:
    return file_path.name.endswith(ALIGNED_ACCELERATION_SUFFIX) or file_path.name.endswith(
        LEGACY_PROCESSED_SUFFIX
    )


def displacement_filename(source_file: Path) -> str:
    stem = source_file.stem
    if stem.endswith("_aligned_acceleration"):
        stem = stem[: -len("_aligned_acceleration")]
    elif stem.endswith("_processed"):
        stem = stem[: -len("_processed")]
    return f"{stem}{DISPLACEMENT_SUFFIX}"
