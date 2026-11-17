# BJT Common-Emitter DC Bias Calculator (Lab 03)

Flask web app for the **ENG29 2121** lab. It computes the DC operating point of
an NPN common-emitter stage in **three** bias circuits and cross-checks the
result with an independent calculation (voltage divider).

- **Voltage Divider Bias** (Lab 2, unchanged) — R₁, R₂, R_E
- **Fixed Bias** (Lab 3) — R_B
- **Emitter Bias** (single supply, Lab 3) — R_B, R_E

## Scope

DC bias only. This lab explicitly does **not** include AC analysis, frequency
response/Bode plots, transient simulation, a circuit editor, or FETs.

## Install and run

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Open <http://127.0.0.1:5000>. Switch circuits with the mode cards at the top of
the page; the form reloads and shows only the fields that circuit needs.

## Inputs

| Input | Meaning | Unit |
|---|---|---|
| `VCC` | supply voltage | V |
| `R1` | upper base resistor (divider) | Ω or kΩ |
| `R2` | lower base resistor (divider) | Ω or kΩ |
| `RB` | base resistor (fixed / emitter) | Ω or kΩ |
| `RC` | collector resistor | Ω or kΩ |
| `RE` | emitter resistor | Ω or kΩ |
| `beta` | transistor current gain | — |
| `VBE` | base-emitter voltage drop | V |

All inputs must be finite numbers. `VCC`, the resistors and `beta` must be
greater than zero; `0 <= VBE < VCC`. Every validation error is shown together.
Resistor values are converted to ohms before the calculation, so `2.2 kΩ` and
`2200 Ω` give the same answer. `RB` is ignored by the voltage-divider circuit.

## Outputs

`VB`, `VE`, `VC`, `VCE` (V), `IB` (µA), `IC` and `IE` (mA), all to two
decimal places. The page also draws the circuit with the entered values and
shows a status box:

- **Cut-off** when `VBB <= VBE` — currents are zero, `VB = VBB`, `VC = VCE = VCC`.
- **Saturation** when `VCE < 0.2 V` — a warning that the fixed-`beta` model is
  not valid there.
- **Active** otherwise.

## Two independent calculations (voltage divider)

1. **Thevenin closed form** — reduce the base divider to `VBB` and `RB`, then
   `IB = (VBB - VBE) / (RB + (beta + 1) * RE)` and derive the rest.
2. **Nodal analysis** — solve the 3×3 system in `VB`, `VE`, `IB` directly with
   Gaussian elimination, without the Thevenin reduction.

`analyze` compares the two at a relative tolerance of `1e-9` and returns
`passed`/`max_abs_diff`; the page no longer prints that line. Fixed and Emitter
Bias use the same `Forward Active` model (β and V_BE constant).

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

41 tests in `tests/` cover parsing, units, regions, overflow and the route.
Lab 03 adds no new automated tests; acceptance is done in the browser (A1–A5).

## Browser acceptance (A1–A5)

Shared constants: V_CC = 12 V, R_C = 2.2 kΩ, β = 100, V_BE = 0.70 V.
Full table, independent hand calculations, evidence screenshots and the
OpenCode MCP note are in [`docs/validation.md`](docs/validation.md).

| Case | Inputs | Expected (hand) | Observed | Status |
|---|---|---|---|---|
| A1 Divider | R₁=100, R₂=22, R_E=1 kΩ | I_C=1.2299 mA, V_CE=8.0522 V | 1.23 mA, 8.05 V | PASS |
| A2 Fixed | R_B=1000 kΩ | I_C=1.1300 mA, V_CE=9.5140 V | 1.13 mA, 9.51 V | PASS |
| A3 Emitter | R_B=1000, R_E=1 kΩ | I_C=1.0263 mA, V_CE=8.7054 V | 1.03 mA, 8.71 V | PASS |
| A4 Emitter | R_B=1000, R_E=2 kΩ | I_C=0.9401 mA (decreases), V_CE=8.0328 V | 0.94 mA, 8.03 V | PASS |
| A5 Fixed | R_B=0 | error message, no stale result | “RB must be greater than zero”, HTTP 400 | PASS |

Playwright MCP was configured in `opencode.json` but could not start on this
machine (no Node.js/npx), so the cases were run with the OpenCode Browser
instead and the blocker is recorded in `docs/validation.md`.

## Design of the page

* **Hero** — navy background with a self-drawn circuit SVG (`static/img/hero.svg`),
  no external image or font dependency, so it works offline.
* **Mode cards** — each card carries a small circuit diagram (`templates/_circuit.html`).
* **Form panel** — inputs with unit selects, plus a sticky panel showing the
  selected circuit and the formula actually used.
* **Result panel** — I_C and V_CE as stat cards, plus gauges for
  V_CE/V_CC and I_C/I_C(sat), the full operating point and the region status.
* Focus rings, `aria-live` on the result, `prefers-reduced-motion` and print
  styles are included.

## What AI created vs. what the student checks

* AI wrote: `bjt_bias.py` extensions (`analyze_fixed`, `analyze_emitter`,
  `analyze_mode`, mode-aware `parse_inputs`), the mode dispatch and unit handling
  in `app.py`, the mode cards / gauges / circuit panel in the template, the
  polished CSS, and the documentation.
* Student checks: the equations against Engineering Electronics, the unit
  conversion (kΩ → Ω) in `app.py`, the `if/elif` dispatch, the behaviour on
  bad input (no stale result), A1–A5 against hand calculations, and one case
  re-run by hand (A3 → A4).

## Git

Commit SHA: `3290d1b` (integration branch `lab03-integrated`, based on the
existing `Gitlab` repo so the original tests and `bjt_bias.py` are preserved).
Push succeeded: https://github.com/0650899746por-creator/Gitlab/tree/lab03-integrated
