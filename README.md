# Accelerometer Calibration

This project reads the three calibration `.txt` files in `input/`, prompts for
two time windows per file, calculates six averaged `(x, y, z)` calibration
points, and fits calibration parameters `(a1, a2, a3, b1, b2, b3)` such that:

`(a1*(x-b1))^2 + (a2*(y-b2))^2 + (a3*(z-b3))^2 = 9.81^2`

The project also supports batch-processing experiment files using a saved
`output/calibration_result.json`. During processing it imports both `gravity`
and `parameters` from the JSON file and applies:

`X = a1*(x-b1), Y = a2*(y-b2), Z = a3*(z-b3)`

to every numeric row in each experiment `.txt` file found in `input/`.

The code is split by responsibility:

- `src/accelerometer_calibration/calibration.py` contains calibration logic
- `src/accelerometer_calibration/processing.py` contains experiment-data processing logic
- `src/accelerometer_calibration/cli.py` contains command-line routing

## Run Calibration

```bash
python main.py
```

Alternative:

```bash
$env:PYTHONPATH = "src"
python -m accelerometer_calibration
```

The calibration workflow will:

1. Discover the three `.txt` files in `input/`
2. Show the time range for each file
3. Ask for `start_time` and `end_time` for `test_1` and `test_2`
4. Print the six averaged calibration points
5. Print the fitted calibration parameters and residual check
6. Save the calibration result to `output/calibration_result.json`

## Run Data Processing

```bash
python main.py process
```

Alternative:

```bash
$env:PYTHONPATH = "src"
python -m accelerometer_calibration process
```

The processing workflow will:

1. Read `output/calibration_result.json`
2. Import `gravity` and `parameters`
3. Discover all experiment `.txt` files in `input/`
4. Ignore the title/header section in each file
5. Read the four numeric columns `(time, x, y, z)`
6. Apply the calibration formula to every row
7. Ask for a stable `start_time,end_time` for each file
8. Average the calibrated `(x, y, z)` values in that stable window
9. Build a rotation matrix that maps the averaged gravity vector to `(0, gravity, 0)`
10. Apply that rotation matrix to all calibrated rows
11. Save the rotated output to `output/` as `*_processed.txt`

## Saved Result

After a calibration run, the project writes `output/calibration_result.json`.
This file contains:

- `a1`, `a2`, `a3`
- `b1`, `b2`, `b3`
- the six averaged calibration points
- the selected time windows
- the corrected norm for each point

This saved file is intended to be reused by later data-analysis steps.
