# Accelerometer Calibration

This project calibrates accelerometer text exports, applies the saved
calibration to experiment files, and converts aligned acceleration data into
displacement output.

## Project Layout

```text
Accelerometer/
|-- input/                                raw calibration and experiment .txt files
|-- output/                               generated calibration and analysis files
|-- src/accelerometer_calibration/
|   |-- cli.py                            command-line entrypoint
|   |-- paths.py                          shared default paths and output names
|   |-- calibration.py                    calibration workflow and JSON save/load
|   |-- processing.py                     calibration application and gravity alignment
|   |-- displacement.py                   acceleration-to-displacement conversion
|   |-- __init__.py
|   `-- __main__.py                       supports python -m accelerometer_calibration
|-- main.py                               compatibility launcher from repo root
`-- pyproject.toml                        package metadata and CLI script
```

## Recommended Command

Install the project once in editable mode:

```bash
python -m pip install -e .
```

After that, use the installed command:

```bash
accelerometer
```

That starts the calibration workflow directly.

Compatibility entrypoints still work:

```bash
python main.py
python -m accelerometer_calibration
```

## Commands

### 1. Calibrate

Default:

```bash
accelerometer
```

Explicit:

```bash
accelerometer calibrate
```

Optional paths:

```bash
accelerometer calibrate --input-dir input --output output/calibration.json
```

This workflow:

1. Reads the 3 calibration `.txt` files in `input/`
2. Prompts for two time windows per file
3. Calculates 6 averaged `(x, y, z)` calibration points
4. Fits calibration parameters `(a1, a2, a3, b1, b2, b3)`
5. Saves the result to `output/calibration.json`

Fitted model:

`(a1*(x-b1))^2 + (a2*(y-b2))^2 + (a3*(z-b3))^2 = 9.81^2`

### 2. Process Experiment Files

```bash
accelerometer process
```

Optional paths:

```bash
accelerometer process --input-dir input --output-dir output --calibration output/calibration.json
```

This workflow:

1. Loads `gravity` and calibration parameters from `calibration.json`
2. Applies `X = a1*(x-b1), Y = a2*(y-b2), Z = a3*(z-b3)` to each numeric row
3. Prompts for a stable time window per file
4. Rotates the data so the average gravity vector aligns to `(0, gravity, 0)`
5. Writes `*_aligned_acceleration.txt` files to `output/`

### 3. Convert Aligned Acceleration to Displacement

Default:

```bash
accelerometer displacement
```

Explicit paths:

```bash
accelerometer displacement --input-dir output --output-dir output
```

This workflow:

1. Reads aligned acceleration files from `output/`
2. Derives the sample rate from the time column
3. Applies high-pass filtering and double integration
4. Writes `*_displacement_mm.txt` files to `output/`

## Output Files

The default generated files are:

- `output/calibration.json`
- `output/<source>_aligned_acceleration.txt`
- `output/<source>_displacement_mm.txt`

The processing and displacement commands still accept the older calibration and
processed-file names if they already exist, but new runs now write the names
above.

## Saved Calibration File

`output/calibration.json` includes:

- `gravity`
- `parameters.a1`, `parameters.a2`, `parameters.a3`
- `parameters.b1`, `parameters.b2`, `parameters.b3`
- averaged calibration points
- selected time windows
- corrected norm for each calibration point
