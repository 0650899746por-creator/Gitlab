# BJT Common-Emitter DC Bias Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimal Flask web app that computes and cross-checks the DC operating point of a voltage-divider-biased BJT common-emitter circuit.

**Architecture:** All engineering math lives in `bjt_bias.py` as pure functions: input parsing/validation, a Thevenin closed-form solver, and an independent 3×3 nodal solver. `app.py` only routes form data into `bjt_bias.analyze()` and renders the returned dict; `templates/index.html` performs no arithmetic and contains no JavaScript.

**Tech Stack:** Python 3.12, Flask 3.x, pytest, Jinja2, plain CSS.

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-ce-bias-design.md`

**Time budget:** ~2.5 hours total (Task 1 ≈ 20 min, Task 2 ≈ 40 min, Task 3 ≈ 30 min, Task 4 ≈ 45 min, Task 5 ≈ 15 min). Five tasks, five commits.

## Global Constraints

- Python 3.12.7 (`python` on PATH); Flask `>=3.1,<4`; pytest `>=8,<9`.
- No numpy, sympy, or other numeric libraries — the 3×3 solver is written in pure Python.
- No JavaScript, no chart library, no CSS framework.
- All math and number formatting happen in `bjt_bias.py`; templates only print values.
- Currents: IB displayed in µA, IC/IE in mA, 3 decimals. Voltages in V, 3 decimals. RB in Ω, 3 decimals.
- Validation error text (exact): `"<LABEL> must be a number."`, `"<LABEL> must be a finite number."`, `"<LABEL> must be greater than zero."`, `"VBE must be between 0 and VCC."`.
- Labels: `VCC`, `R1`, `R2`, `RC`, `RE`, `beta`, `VBE`.
- Region labels: `"Cut-off region"`, `"Active region"`, `"Saturation region"`.
- Saturation threshold `VCE_SAT_V = 0.2`; verification relative tolerance `REL_TOL = 1e-9`.
- Dev server: `127.0.0.1:5000`.
- `git` is not on PATH. Every git command uses `& "C:\Users\B6828417\AppData\Local\Programs\Git\cmd\git.exe"`.
- Tests run as `.venv\Scripts\python.exe -m pytest`.
- Do not modify `electrical.py` or `test_electrical.py`.

## Review Focus

1. **Blank or non-numeric field** — a person expects a readable field error and HTTP 200, never a traceback. Tested in Task 1 (`test_parse_rejects_non_numeric_and_missing`).
2. **Cut-off bias (VBB ≤ VBE)** — a person expects zero currents and no negative current shown. Tested in Tasks 2 and 3 (`test_closed_form_cutoff_returns_zero_currents`, `test_analyze_cutoff_region_and_warning`).
3. **RC large enough to drive VCE below 0.2 V** — a person expects the computed point plus a saturation warning, not a crash. Tested in Task 3 (`test_analyze_saturation_region_and_warning`).
4. **Zero or negative R / beta** — a person expects a validation error, not `ZeroDivisionError`. Tested in Task 1 (`test_parse_rejects_out_of_range`).
5. **Extreme magnitudes (`1e400`)** — a person expects a finite-number validation error, never `inf`/`nan` on the page. Tested in Task 1 (`test_parse_rejects_non_finite`).

---

### Task 1: Scaffold, requirements, and input parsing/validation

**Files:**
- Create: `requirements.txt`
- Create: `bjt_bias.py`
- Create: `tests/test_bjt_bias.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `REQUIRED_FIELDS: tuple[str, ...]` = `("vcc", "r1", "r2", "rc", "re", "beta", "vbe")`
  - `LABELS: dict[str, str]` mapping each field to its display label
  - `parse_inputs(raw: Mapping[str, str]) -> tuple[dict[str, float] | None, list[str]]` — returns `(values, [])` when valid, `(None, errors)` otherwise; collects all errors.

- [ ] **Step 1: Create the virtual environment and install dependencies**

Create `requirements.txt`:

```text
Flask>=3.1,<4
pytest>=8,<9
```

Run:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Expected: pip reports Flask and pytest installed.

- [ ] **Step 2: Write the failing validation tests**

Create `tests/test_bjt_bias.py`:

```python
import pytest

from bjt_bias import parse_inputs

VALID = {
    "vcc": "12",
    "r1": "47000",
    "r2": "10000",
    "rc": "2200",
    "re": "470",
    "beta": "150",
    "vbe": "0.7",
}


def test_parse_valid_returns_floats():
    values, errors = parse_inputs(VALID)
    assert errors == []
    assert values["vcc"] == 12.0
    assert values["beta"] == 150.0


def test_parse_rejects_non_numeric_and_missing():
    values, errors = parse_inputs({**VALID, "rc": "abc"})
    assert values is None
    assert any("RC" in error for error in errors)

    values, errors = parse_inputs({k: v for k, v in VALID.items() if k != "vbe"})
    assert values is None
    assert any("VBE" in error for error in errors)


@pytest.mark.parametrize(
    "field,value,label",
    [
        ("vcc", "0", "VCC"),
        ("r1", "0", "R1"),
        ("r2", "-1", "R2"),
        ("rc", "0", "RC"),
        ("re", "0", "RE"),
        ("beta", "0", "beta"),
        ("vbe", "12", "VBE"),
    ],
)
def test_parse_rejects_out_of_range(field, value, label):
    values, errors = parse_inputs({**VALID, field: value})
    assert values is None
    assert any(label in error for error in errors)


def test_parse_collects_all_errors():
    values, errors = parse_inputs({**VALID, "r1": "-1", "rc": "0", "beta": "0"})
    assert values is None
    assert len(errors) == 3


def test_parse_rejects_non_finite():
    values, errors = parse_inputs({**VALID, "r1": "1e400"})
    assert values is None
    assert any("finite" in error.lower() for error in errors)
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_bjt_bias.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'bjt_bias'`.

- [ ] **Step 4: Implement `parse_inputs` in `bjt_bias.py`**

Create `bjt_bias.py` with `REQUIRED_FIELDS`, `LABELS`, and (importing `Mapping` from `collections.abc`):

```python
def parse_inputs(raw: Mapping[str, str]) -> tuple[dict[str, float] | None, list[str]]:
    ...
```

Behavior: for each field, read `raw.get(field, "").strip()`; `float()` it; on `ValueError` append `f"{LABELS[field]} must be a number."`; on non-finite append `f"{LABELS[field]} must be a finite number."`. Then range checks: `vcc > 0`, `r1/r2/rc/re > 0`, `beta > 0` all use `f"{LABELS[field]} must be greater than zero."`; `0 <= vbe < vcc` uses `"VBE must be between 0 and VCC."`. Return `(None, errors)` if any errors, else `(values, [])`.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_bjt_bias.py -v`

Expected: 11 passed (4 plain tests + 7 parametrized cases).

- [ ] **Step 6: Commit**

```powershell
& "C:\Users\B6828417\AppData\Local\Programs\Git\cmd\git.exe" add requirements.txt bjt_bias.py tests/test_bjt_bias.py
& "C:\Users\B6828417\AppData\Local\Programs\Git\cmd\git.exe" commit -m "feat: add BJT bias input validation"
```

---

### Task 2: Thevenin closed-form and independent nodal solvers

**Files:**
- Modify: `bjt_bias.py`
- Modify: `tests/test_bjt_bias.py`

**Interfaces:**
- Consumes: nothing from Task 1 (pure math; validation is separate).
- Produces:
  - `closed_form(vcc, r1, r2, rc, re, beta, vbe) -> dict[str, float]`
  - `nodal(vcc, r1, r2, rc, re, beta, vbe) -> dict[str, float]`
  - both return the same keys: `ib_a, ic_a, ie_a, vb_v, ve_v, vc_v, vce_v, vbb_v, rb_ohm`
  - `_solve_3x3(matrix: list[list[float]], rhs: list[float]) -> list[float]`

- [ ] **Step 1: Write the failing solver tests**

Append to `tests/test_bjt_bias.py`:

```python
from bjt_bias import closed_form, nodal


def test_closed_form_known_values():
    result = closed_form(12, 47000, 10000, 2200, 470, 150, 0.7)
    assert result["ib_a"] == pytest.approx(1.77397243587898e-05, rel=1e-9)
    assert result["ic_a"] == pytest.approx(0.0026609586538184696, rel=1e-9)
    assert result["ie_a"] == pytest.approx(0.0026786983781772597, rel=1e-9)
    assert result["ve_v"] == pytest.approx(1.2589882377433121, rel=1e-9)
    assert result["vb_v"] == pytest.approx(1.958988237743312, rel=1e-9)
    assert result["vc_v"] == pytest.approx(6.145890961599367, rel=1e-9)
    assert result["vce_v"] == pytest.approx(4.886902723856055, rel=1e-9)
    assert result["vbb_v"] == pytest.approx(2.1052631578947367, rel=1e-9)
    assert result["rb_ohm"] == pytest.approx(8245.61403508772, rel=1e-9)


def test_closed_form_cutoff_returns_zero_currents():
    result = closed_form(12, 47000, 1000, 2200, 470, 150, 0.7)
    assert result["ib_a"] == 0
    assert result["ic_a"] == 0
    assert result["ie_a"] == 0
    assert result["vb_v"] == pytest.approx(0.25)
    assert result["vc_v"] == 12
    assert result["vce_v"] == 12


def test_nodal_matches_closed_form():
    cases = [
        (12, 47000, 10000, 2200, 470, 150, 0.7),
        (5, 10000, 2200, 1000, 100, 100, 0.65),
        (15, 68000, 12000, 3300, 680, 200, 0.7),
        (9, 22000, 4700, 1500, 330, 80, 0.6),
        (24, 100000, 15000, 4700, 1000, 300, 0.7),
    ]
    for case in cases:
        expected = closed_form(*case)
        actual = nodal(*case)
        for key in expected:
            scale = max(1.0, abs(expected[key]), abs(actual[key]))
            assert abs(expected[key] - actual[key]) <= 1e-9 * scale, key


def test_nodal_cutoff_matches_closed_form():
    result = nodal(12, 47000, 1000, 2200, 470, 150, 0.7)
    assert result["ic_a"] == 0
    assert result["vb_v"] == pytest.approx(0.25)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_bjt_bias.py -k "closed_form or nodal" -v`

Expected: FAIL with `ImportError: cannot import name 'closed_form'`.

- [ ] **Step 3: Implement `closed_form`**

Signature: `def closed_form(vcc: float, r1: float, r2: float, rc: float, re: float, beta: float, vbe: float) -> dict[str, float]:`

Use the spec's equations. If `ib <= 0`, return the cut-off dict: `ib_a=ic_a=ie_a=0`, `ve_v=0`, `vb_v=vbb_v`, `vc_v=vce_v=vcc`, `vbb_v = vcc*r2/(r1+r2)`, `rb_ohm = r1*r2/(r1+r2)`. Otherwise compute the active dict from the spec.

- [ ] **Step 4: Run the closed-form tests**

Run: `.venv\Scripts\python.exe -m pytest tests/test_bjt_bias.py -k closed_form -v`

Expected: 2 passed.

- [ ] **Step 5: Implement `_solve_3x3` and `nodal`**

Build the 3×3 system from the spec:

```text
row 0: [ 1, -1,  0 ]                         rhs: vbe
row 1: [ -1/r1 - 1/r2, 0, -1 ]               rhs: -vcc/r1
row 2: [ 0, -1/re, beta + 1 ]                rhs: 0
```

Solve with Gaussian elimination and partial pivoting (swap the row with the largest absolute pivot, eliminate below, back-substitute). Unknowns are `vb_v, ve_v, ib_a` in that order.

After solving, `ib <= 0` means cut-off: return the same clamped dict as `closed_form`. Otherwise compute `ic_a = beta*ib`, `ie_a = (beta+1)*ib`, `vc_v = vcc - ic*rc`, `vce_v = vc_v - ve_v`, `vbb_v = vcc*r2/(r1+r2)`, `rb_ohm = r1*r2/(r1+r2)`.

- [ ] **Step 6: Run the solver tests**

Run: `.venv\Scripts\python.exe -m pytest tests/test_bjt_bias.py -k "closed_form or nodal" -v`

Expected: 4 passed.

- [ ] **Step 7: Commit**

```powershell
& "C:\Users\B6828417\AppData\Local\Programs\Git\cmd\git.exe" add bjt_bias.py tests/test_bjt_bias.py
& "C:\Users\B6828417\AppData\Local\Programs\Git\cmd\git.exe" commit -m "feat: add closed-form and nodal bias solvers"
```

---

### Task 3: `analyze`, region warnings, display strings, verification

**Files:**
- Modify: `bjt_bias.py`
- Modify: `tests/test_bjt_bias.py`

**Interfaces:**
- Consumes: `closed_form` and `nodal` from Task 2.
- Produces:
  - `VCE_SAT_V = 0.2`, `REL_TOL = 1e-9`
  - `to_display(values: dict[str, float]) -> dict[str, str]` with keys `ib_ua, ic_ma, ie_ma, vb_v, ve_v, vc_v, vce_v, vbb_v, rb_ohm`
  - `analyze(vcc, r1, r2, rc, re, beta, vbe) -> dict` returning:
    - `values`: dict with the 9 numeric keys
    - `display`: output of `to_display(values)`
    - `region`: `"cutoff" | "active" | "saturation"`
    - `region_label`: `"Cut-off region" | "Active region" | "Saturation region"`
    - `warnings`: list of strings
    - `verification`: `{"closed_form": dict, "nodal": dict, "max_abs_diff": float, "passed": bool}`

- [ ] **Step 1: Write the failing analyze tests**

Append to `tests/test_bjt_bias.py`:

```python
from bjt_bias import analyze


def test_analyze_example_active_and_verification_passes():
    result = analyze(12, 47000, 10000, 2200, 470, 150, 0.7)
    assert result["region"] == "active"
    assert result["region_label"] == "Active region"
    assert result["warnings"] == []
    assert result["verification"]["passed"] is True
    assert result["verification"]["max_abs_diff"] <= 1e-9
    assert result["display"]["ib_ua"] == "17.740"
    assert result["display"]["ic_ma"] == "2.661"
    assert result["display"]["ie_ma"] == "2.679"
    assert result["display"]["vb_v"] == "1.959"
    assert result["display"]["ve_v"] == "1.259"
    assert result["display"]["vc_v"] == "6.146"
    assert result["display"]["vce_v"] == "4.887"
    assert result["display"]["vbb_v"] == "2.105"
    assert result["display"]["rb_ohm"] == "8245.614"


def test_analyze_cutoff_region_and_warning():
    result = analyze(12, 47000, 1000, 2200, 470, 150, 0.7)
    assert result["region"] == "cutoff"
    assert result["region_label"] == "Cut-off region"
    assert any("cut off" in warning.lower() for warning in result["warnings"])
    assert result["display"]["ic_ma"] == "0.000"


def test_analyze_saturation_region_and_warning():
    result = analyze(12, 47000, 10000, 4700, 470, 150, 0.7)
    assert result["region"] == "saturation"
    assert result["region_label"] == "Saturation region"
    assert any("saturation" in warning.lower() for warning in result["warnings"])
    assert result["display"]["vce_v"] == "-1.765"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_bjt_bias.py -k analyze -v`

Expected: FAIL with `ImportError: cannot import name 'analyze'`.

- [ ] **Step 3: Implement `to_display` and `analyze`**

`to_display` formats `ib_a * 1e6` and `ic_a/ie_a * 1e3` with `f"{value:.3f}"`; voltages and `rb_ohm` with `f"{value:.3f}"`.

`analyze` computes both solvers, takes `values = closed_form(...)`, computes `max_abs_diff` over all 9 keys, and sets `passed = all(abs(a - b) <= REL_TOL * max(1.0, abs(a), abs(b)))`.

Region: if `values["vbb_v"] <= vbe` → `cutoff`, warning `"Transistor is cut off (VBB <= VBE): IB = IC = IE = 0."`; elif `values["vce_v"] < VCE_SAT_V` → `saturation`, warning `"Transistor is in saturation (VCE < 0.2 V); the fixed-beta model is not valid."`; else `active` with no warnings.

- [ ] **Step 4: Run all logic tests**

Run: `.venv\Scripts\python.exe -m pytest tests/test_bjt_bias.py -v`

Expected: 18 passed.

- [ ] **Step 5: Commit**

```powershell
& "C:\Users\B6828417\AppData\Local\Programs\Git\cmd\git.exe" add bjt_bias.py tests/test_bjt_bias.py
& "C:\Users\B6828417\AppData\Local\Programs\Git\cmd\git.exe" commit -m "feat: add bias analysis with region warnings and cross-check"
```

---

### Task 4: Flask app, template, CSS, and route tests

**Files:**
- Create: `app.py`
- Create: `templates/index.html`
- Create: `static/style.css`
- Create: `tests/test_app.py`

**Interfaces:**
- Consumes: `parse_inputs`, `analyze` from `bjt_bias` (imported as `import bjt_bias`, never `from bjt_bias import analyze`, so tests can monkeypatch).
- Produces: `create_app() -> Flask`, module-level `app`, `DEFAULT_FORM: dict[str, str]`.

- [ ] **Step 1: Write the failing route tests**

Create `tests/test_app.py`:

```python
import pytest

import app as app_module

VALID = {
    "vcc": "12",
    "r1": "47000",
    "r2": "10000",
    "rc": "2200",
    "re": "470",
    "beta": "150",
    "vbe": "0.7",
}


@pytest.fixture()
def client():
    app_module.app.config.update(TESTING=True)
    return app_module.app.test_client()


def test_get_shows_all_inputs(client):
    html = client.get("/").get_data(as_text=True)
    for name in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"):
        assert f'name="{name}"' in html


def test_post_valid_shows_computed_values(client):
    html = client.post("/", data=VALID).get_data(as_text=True)
    assert "17.740" in html
    assert "2.661" in html
    assert "4.887" in html
    assert "Active region" in html
    assert "PASS" in html


def test_post_invalid_shows_error_without_results(client):
    html = client.post("/", data={**VALID, "vcc": "0"}).get_data(as_text=True)
    assert "VCC must be greater than zero" in html
    assert "Operating point" not in html


def test_route_uses_backend_analyze(client, monkeypatch):
    fake = {
        "values": {
            "ib_a": 0.0, "ic_a": 0.0, "ie_a": 0.0,
            "vb_v": 0.0, "ve_v": 0.0, "vc_v": 0.0, "vce_v": 0.0,
            "vbb_v": 0.0, "rb_ohm": 0.0,
        },
        "display": {
            "ib_ua": "1.000", "ic_ma": "999.999", "ie_ma": "1.000",
            "vb_v": "0.000", "ve_v": "0.000", "vc_v": "0.000",
            "vce_v": "0.000", "vbb_v": "0.000", "rb_ohm": "0.000",
        },
        "region": "active",
        "region_label": "Active region",
        "warnings": [],
        "verification": {"closed_form": {}, "nodal": {}, "max_abs_diff": 0.0, "passed": True},
    }
    monkeypatch.setattr(app_module.bjt_bias, "analyze", lambda **kwargs: fake)
    html = client.post("/", data=VALID).get_data(as_text=True)
    assert "999.999" in html


def test_page_has_no_javascript(client):
    html = client.get("/").get_data(as_text=True)
    assert "<script" not in html.lower()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_app.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'app'`.

- [ ] **Step 3: Implement `app.py`**

```python
import bjt_bias
from flask import Flask, render_template, request

DEFAULT_FORM = {
    "vcc": "12", "r1": "47000", "r2": "10000", "rc": "2200",
    "re": "470", "beta": "150", "vbe": "0.7",
}


def create_app() -> Flask:
    ...


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
```

`create_app` registers one route, `"/"`, methods `GET` and `POST`. On GET: render `index.html` with `form=DEFAULT_FORM`, `errors=[]`, `result=None`. On POST: `values, errors = bjt_bias.parse_inputs(request.form)`; if `values` is not None, `result = bjt_bias.analyze(**values)`; build `form` from `request.form` falling back to `DEFAULT_FORM` for missing keys; render.

- [ ] **Step 4: Implement `templates/index.html` and `static/style.css`**

Template requirements:
- Link `style.css` via `url_for`.
- Form posts to `"/"` with one labelled numeric input per field (`name="vcc"` … `name="vbe"`), values from `form`.
- Error list rendered when `errors` is non-empty.
- Results block wrapped in `{% if result %}` and headed with the exact text `Operating point`.
- Show `result.display.ib_ua` µA, `result.display.ic_ma`/`ie_ma` mA, `result.display.vb_v`/`ve_v`/`vc_v`/`vce_v` V, `result.display.vbb_v` V, `result.display.rb_ohm` Ω.
- Show `result.region_label`, each string in `result.warnings`, and a verification line containing `PASS` when `result.verification.passed` else `FAIL`, plus `result.verification.max_abs_diff`.
- No `<script>` tag, no arithmetic expressions.

CSS: plain stylesheet, ~60–80 lines: system font, centered column max-width ~720px, visible labels, table borders, distinct colors for `.region-active`, `.region-cutoff`, `.region-saturation`. No framework, no images.

- [ ] **Step 5: Run the route tests**

Run: `.venv\Scripts\python.exe -m pytest tests/test_app.py -v`

Expected: 5 passed.

- [ ] **Step 6: Commit**

```powershell
& "C:\Users\B6828417\AppData\Local\Programs\Git\cmd\git.exe" add app.py templates static tests/test_app.py
& "C:\Users\B6828417\AppData\Local\Programs\Git\cmd\git.exe" commit -m "feat: add Flask UI for BJT bias calculator"
```

---

### Task 5: README, final verification, and push

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: the finished app.
- Produces: nothing other tasks use.

- [ ] **Step 1: Rewrite `README.md`**

Include: what the app is (ENG29 2121 BJT CE DC bias lab), install/run commands, the 7 inputs and units, the two calculation methods, region rules (`VBB <= VBE` cut-off, `VCE < 0.2 V` saturation), how to run tests, the explicit non-goals (no AC/Bode/transient/editor/FET), and a note that `electrical.py` is the legacy DC calculator.

- [ ] **Step 2: Run the full test suite**

Run: `.venv\Scripts\python.exe -m pytest -q`

Expected: 23 passed, no failures.

- [ ] **Step 3: Verify the app on localhost**

Run in the background:

```powershell
.venv\Scripts\python.exe app.py
```

Then verify GET and a POST with the sample values:

```powershell
(Invoke-WebRequest -UseBasicParsing http://127.0.0.1:5000/).StatusCode
$body = @{vcc="12"; r1="47000"; r2="10000"; rc="2200"; re="470"; beta="150"; vbe="0.7"}
$html = (Invoke-WebRequest -UseBasicParsing -Method Post -Uri http://127.0.0.1:5000/ -Body $body).Content
$html -match "2\.661"; $html -match "4\.887"; $html -match "Active region"; $html -match "PASS"
```

Expected: `200`, then four `True` lines. Stop the server afterward.

- [ ] **Step 4: Commit and push**

```powershell
& "C:\Users\B6828417\AppData\Local\Programs\Git\cmd\git.exe" add README.md
& "C:\Users\B6828417\AppData\Local\Programs\Git\cmd\git.exe" commit -m "docs: describe BJT bias lab app"
& "C:\Users\B6828417\AppData\Local\Programs\Git\cmd\git.exe" push origin main
```

Expected: push succeeds. If authentication fails, report the exact error and stop — do not rewrite history.
