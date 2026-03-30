# Accelerometer Calibration

This project reads the three calibration `.txt` files in `input/`, prompts for
two time windows per file, calculates six averaged `(x, y, z)` calibration
points, and fits calibration parameters `(a1, a2, a3, b1, b2, b3)` such that:

`(a1*(x-b1))^2 + (a2*(y-b2))^2 + (a3*(z-b3))^2 = 9.81^2`

## Run

```bash
python main.py
```

Alternative:

```bash
$env:PYTHONPATH = "src"
python -m accelerometer_calibration
```

The script will:

1. Discover the three `.txt` files in `input/`
2. Show the time range for each file
3. Ask for `start_time` and `end_time` for `test_1` and `test_2`
4. Print the six averaged calibration points
5. Print the fitted calibration parameters and residual check
6. Save the calibration result to `output/calibration_result.json`

## Saved Result

After a calibration run, the project writes `output/calibration_result.json`.
This file contains:

- `a1`, `a2`, `a3`
- `b1`, `b2`, `b3`
- the six averaged calibration points
- the selected time windows
- the corrected norm for each point

This saved file is intended to be reused by later data-analysis steps.
