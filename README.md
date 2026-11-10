# BJT Common-Emitter DC Bias Calculator

Minimal Flask web app for the **ENG29 2121** lab. It computes the DC operating
point of a voltage-divider-biased NPN common-emitter stage and cross-checks the
result with an independent calculation.

## Scope

DC bias only. This lab explicitly does **not** include AC analysis, frequency
response/Bode plots, transient simulation, a circuit editor, or FETs.

## Install and run

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

Open <http://127.0.0.1:5000>.

## Inputs

| Input | Meaning | Unit |
|---|---|---|
| `VCC` | supply voltage | V |
| `R1` | upper base resistor | Ω or kΩ |
| `R2` | lower base resistor | Ω or kΩ |
| `RC` | collector resistor | Ω or kΩ |
| `RE` | emitter resistor | Ω or kΩ |
| `beta` | transistor current gain | — |
| `VBE` | base-emitter voltage drop | V |

All inputs must be finite numbers. `VCC`, the resistors, and `beta` must be
greater than zero; `0 <= VBE < VCC`. Every validation error is shown together.
Resistor values are converted to ohms before the calculation, so `2.2 kΩ` and
`2200 Ω` give the same answer.

## Outputs

`VB`, `VE`, `VC`, `VCE` (V), `IB` (µA), `IC` and `IE` (mA), all to two decimal
places. The page also draws the circuit with the entered values.

Operating region, shown as a coloured status box:

- **Cut-off** when `VBB <= VBE` — currents are zero, `VB = VBB`, `VC = VCE = VCC`.
- **Saturation** when `VCE < 0.2 V` — a warning that the fixed-`beta` model is
  not valid there.
- **Active** otherwise.

## Two independent calculations

1. **Thevenin closed form** — reduce the base divider to `VBB` and `RB`, then
   `IB = (VBB - VBE) / (RB + (beta + 1) * RE)` and derive the rest.
2. **Nodal analysis** — solve the 3×3 system in `VB`, `VE`, `IB` directly with
   Gaussian elimination, without using the Thevenin reduction.

`analyze` compares the two at a relative tolerance of `1e-9` and returns
`passed`/`max_abs_diff`; the page no longer prints that line.

## Tests

```powershell
.venv\Scripts\python.exe -m pytest -q
```

## Files

- `bjt_bias.py` — parsing, validation, both solvers, region logic, formatting
- `app.py` — Flask app factory and the single `/` route
- `templates/index.html`, `static/style.css` — server-rendered UI, no JavaScript
- `static/circuit.svg` — schematic of the voltage-divider-biased stage
- `tests/test_bjt_bias.py` — logic, validation, region, and cross-check tests
- `tests/test_app.py` — route tests, including proof that the backend computes
- `electrical.py`, `test_electrical.py` — legacy DC (V, R) calculator, unused by
  this app
