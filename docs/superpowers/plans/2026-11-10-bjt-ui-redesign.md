# UI Redesign and Resistor Units — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let each resistor be entered in Ω or kΩ, show 2-decimal results, and restyle the page to match the lab mockup (header + three cards + circled-NPN schematic with live values).

**Architecture:** Units are converted to base units (Ω, V) inside `parse_inputs`, so every solver keeps working in SI. Display formatting and the region sentence move into `bjt_bias.analyze`. The web layer builds a `circuit` dict of preformatted strings and includes an inline SVG template.

**Tech Stack:** Python 3.12, Flask 3, Jinja2, pytest 8, hand-authored SVG, plain CSS.

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-ui-redesign-design.md`

## Global Constraints

- No JavaScript anywhere in the page.
- All displayed results use exactly 2 decimal places with a unit.
- The backend remains the only source of numbers; the template prints, never computes.
- Existing behaviour that must survive: validation messages, cut-off/saturation warnings, overflow `ValueError`, and the closed-form vs nodal cross-check in `analyze` (hidden from the page).
- Palette: page `#eef2f7`, cards `#ffffff`, accent teal `#0f7b8a`, text `#1f2933`, muted `#5b6b7b`, success `#e8f7ec`/`#1d6f42`, warning `#fdf3d8`/`#8a6d1d`, danger `#fbe9e9`/`#a12f2f`.

## Review Focus

1. **Unit mismatch** — a person enters `2.2` with `kΩ` and expects the same answer as `2200` with `Ω`.
2. **Unit lost on submit** — a person expects the dropdown to keep the unit they picked after Calculate.
3. **Bad unit value** — a person expects a field error, not a crash, if a unit is missing or unknown.
4. **Two decimals everywhere** — a person expects `8.05 V`, not `8.0523` or `8.1`.
5. **Status box truthfulness** — a person expects the box colour and sentence to match the computed region.

---

### Task 1: Unit-aware input parsing

**Files:**
- Modify: `bjt_bias.py` (constants + `parse_inputs`)
- Test: `tests/test_bjt_bias.py`

**Interfaces:**
- Consumes: nothing new.
- Produces:
  - `UNITS: dict[str, tuple[str, ...]]`
  - `UNIT_FACTORS: dict[str, float]` — `{"V": 1.0, "Ω": 1.0, "kΩ": 1000.0}`
  - `DEFAULT_UNITS: dict[str, str]`
  - `parse_inputs(raw: Mapping[str, str], units: Mapping[str, str] | None = None) -> tuple[dict[str, float] | None, list[str]]` — values returned in base units.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_bjt_bias.py`:

```python
def test_parse_kilo_ohm_matches_ohm():
    ohms, _ = parse_inputs({**VALID, "r1": "47000", "r2": "10000", "rc": "2200", "re": "470"})
    kilos, errors = parse_inputs(
        {**VALID, "r1": "47", "r2": "10", "rc": "2.2", "re": "0.47"},
        {"r1": "kΩ", "r2": "kΩ", "rc": "kΩ", "re": "kΩ"},
    )
    assert errors == []
    assert kilos == ohms


def test_parse_rejects_unknown_unit():
    values, errors = parse_inputs(VALID, {"r1": "MΩ"})
    assert values is None
    assert any("R1" in error and "unit" in error.lower() for error in errors)


def test_parse_defaults_to_kilo_ohm_for_resistors():
    values, errors = parse_inputs({**VALID, "r1": "47", "r2": "10", "rc": "2.2", "re": "0.47"})
    assert errors == []
    assert values["r1"] == pytest.approx(47000.0)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_bjt_bias.py -k "kilo or unknown_unit or defaults_to_kilo" -v`
Expected: FAIL — `parse_inputs` takes no `units` argument.

- [ ] **Step 3: Implement the unit layer in `bjt_bias.py`**

Add the three constants after `LABELS`. In `parse_inputs`, accept `units=None`,
merge over `DEFAULT_UNITS`, and for each field: resolve the unit, reject one
that is not in `UNITS[field]` with `f"{label} unit is not supported."`, then
multiply the parsed float by `UNIT_FACTORS[unit]` before the existing range
checks. `beta` has an empty unit tuple and a factor of 1.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_bjt_bias.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add bjt_bias.py tests/test_bjt_bias.py
git commit -m "feat: accept ohm and kilo-ohm resistor units"
```

---

### Task 2: Two-decimal display and a computed region sentence

**Files:**
- Modify: `bjt_bias.py` (`to_display`, `analyze`)
- Test: `tests/test_bjt_bias.py`

**Interfaces:**
- Consumes: Task 1's `parse_inputs`.
- Produces:
  - `to_display(values) -> dict[str, str]` with exactly `ib_ua, ic_ma, ie_ma, vb_v, ve_v, vc_v, vce_v`, each `f"{x:.2f}"`.
  - `analyze(...)["region_detail"]: str` — e.g. `"VCE = 8.05 V > 0.2 V (transistor in active region)"`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_bjt_bias.py`:

```python
def test_to_display_uses_two_decimals():
    result = analyze(12, 47000, 10000, 2200, 470, 150, 0.7)
    assert result["display"]["ic_ma"] == "2.66"
    assert result["display"]["vce_v"] == "4.89"
    assert result["display"]["ib_ua"] == "17.74"
    assert set(result["display"]) == {
        "ib_ua", "ic_ma", "ie_ma", "vb_v", "ve_v", "vc_v", "vce_v",
    }


def test_analyze_region_detail_matches_region():
    active = analyze(12, 47000, 10000, 2200, 470, 150, 0.7)
    assert active["region_detail"].startswith("VCE = 4.89 V > 0.2 V")

    cutoff = analyze(12, 47000, 1000, 2200, 470, 150, 0.7)
    assert "cut off" in cutoff["region_detail"].lower()

    sat = analyze(12, 47000, 10000, 4700, 470, 150, 0.7)
    assert "saturation" in sat["region_detail"].lower()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_bjt_bias.py -k "two_decimals or region_detail" -v`
Expected: FAIL — three-decimal strings, no `region_detail`.

- [ ] **Step 3: Implement the formatting and sentence**

Change `to_display` to the seven keys with `:.2f`. In `analyze`, build
`region_detail` in each branch from the already-computed numbers:
active `f"VCE = {display['vce_v']} V > 0.2 V (transistor in active region)"`,
cut-off `f"VBB = {display['vbb_v']} V ≤ VBE = {vbe:.2f} V (no collector current)"`,
saturation `f"VCE = {display['vce_v']} V < 0.2 V (fixed-beta model not valid)"`.
Keep `values` and `verification` unchanged. Return `region_detail`.

- [ ] **Step 4: Update the existing tests that asserted three decimals**

In `test_analyze_example_active_and_verification_passes`, change every
`display` assertion to two decimals and drop the `vbb_v`/`rb_ohm` display
assertions. In `test_analyze_cutoff_region_and_warning` change `"0.000"` to
`"0.00"`; in `test_analyze_saturation_region_and_warning` change `"-1.765"`
to `"-1.77"`.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_bjt_bias.py -v`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add bjt_bias.py tests/test_bjt_bias.py
git commit -m "feat: format results to two decimals and add region detail"
```

---

### Task 3: Mockup layout, unit selects, and live schematic

**Files:**
- Modify: `app.py`
- Rewrite: `templates/index.html`
- Create: `templates/_circuit.svg`
- Rewrite: `static/style.css`
- Delete: `static/circuit.svg`
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: `parse_inputs(raw, units)`, `analyze`, `to_display` from Tasks 1–2.
- Produces: `DEFAULT_FORM`, `DEFAULT_UNITS`-driven form, `circuit` template dict with keys `vcc, r1, r2, rc, re, beta`.

- [ ] **Step 1: Write the failing route tests**

Replace the circuit tests and update the value assertions in
`tests/test_app.py`:

```python
def test_page_has_unit_selects(client):
    html = client.get("/").get_data(as_text=True)
    for name in ("unit_r1", "unit_r2", "unit_rc", "unit_re"):
        assert f'name="{name}"' in html
    assert "kΩ" in html
    assert "Ω" in html


def test_kilo_ohm_and_ohm_post_give_same_result(client):
    kilos = client.post("/", data={**VALID_KILO}).get_data(as_text=True)
    ohms = client.post("/", data={**VALID_OHM}).get_data(as_text=True)
    for text in ("1.23", "8.05", "Active region approximation OK"):
        assert text in kilos
        assert text in ohms


def test_results_use_two_decimals(client):
    html = client.post("/", data=VALID_KILO).get_data(as_text=True)
    assert "1.23 mA" in html
    assert "8.05 V" in html
    assert "8.0523" not in html
    assert 'class="status status-active"' in html


def test_selected_unit_is_preserved(client):
    html = client.post("/", data={**VALID_OHM, "unit_r1": "Ω"}).get_data(as_text=True)
    assert '<option value="Ω" selected>' in html


def test_page_shows_live_circuit_values(client):
    html = client.post("/", data=VALID_KILO).get_data(as_text=True)
    assert 'class="circuit-svg"' in html
    assert "VCC = 12 V" in html
    assert "100 kΩ" in html
    assert "2.2 kΩ" in html
    assert "β = 100" in html


def test_page_hides_cross_check(client):
    html = client.post("/", data=VALID_KILO).get_data(as_text=True)
    assert "max |Δ|" not in html
```

with fixtures at the top of the file:

```python
VALID_KILO = {
    "vcc": "12", "r1": "100", "r2": "22", "rc": "2.2", "re": "1.0",
    "beta": "100", "vbe": "0.7",
    "unit_r1": "kΩ", "unit_r2": "kΩ", "unit_rc": "kΩ", "unit_re": "kΩ",
}
VALID_OHM = {
    "vcc": "12", "r1": "100000", "r2": "22000", "rc": "2200", "re": "1000",
    "beta": "100", "vbe": "0.7",
    "unit_r1": "Ω", "unit_r2": "Ω", "unit_rc": "Ω", "unit_re": "Ω",
}
```

Delete `test_page_shows_circuit_figure` and
`test_circuit_asset_is_svg_with_labels`; update the older
`test_post_valid_shows_computed_values` and `test_route_uses_backend_analyze`
to the new defaults and seven-key display dict.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_app.py -v`
Expected: failures on the new tests (no unit selects, no live values).

- [ ] **Step 3: Update `app.py`**

Set `DEFAULT_FORM` to the mockup values (`12`, `100`, `22`, `2.2`, `1.0`,
`100`, `0.7`). On POST collect `units = {field: request.form.get(f"unit_{field}", DEFAULT_UNITS[field])}`
and pass it to `parse_inputs`. Build `circuit` from the submitted text and
unit with a helper that trims trailing zeros (`100 kΩ`, `2.2 kΩ`, `1.0 kΩ`,
`12 V`, `100`); on GET build it from `DEFAULT_FORM`/`DEFAULT_UNITS`. Pass
`units`, `circuit`, and `DEFAULT_UNITS` to the template.

- [ ] **Step 4: Create `templates/_circuit.svg`**

Inline SVG, `viewBox="0 0 360 420"`, `class="circuit-svg"`, `role="img"` with
`<title>`/`<desc>`. Zigzag resistors (US style), circled NPN with an emitter
arrow pointing away from the base, node dot at the base junction, grounds
under R2 and RE. Print `{{ circuit.vcc }}`, `{{ circuit.r1 }}`, `{{ circuit.r2 }}`,
`{{ circuit.rc }}`, `{{ circuit.re }}`, `{{ circuit.beta }}` as text.

- [ ] **Step 5: Rewrite `templates/index.html`**

Header (chip icon, `Lab 02: BJT DC Bias Web App`, `ENG29 2121 – Common
Emitter (Voltage Divider Bias)`, course badge), then a three-card grid:
Input Parameters (rows with label, number input, unit select, teal Calculate
button), Circuit (`{% include "_circuit.svg" %}`), DC Bias Results (seven-row
table at 2 decimals and the region status box). Errors render inside the
input card. No `<script>`, no cross-check line.

- [ ] **Step 6: Rewrite `static/style.css`**

Implement the palette and grid from Global Constraints: three columns above
960px, single column below; cards with 10px radius and soft shadow; teal
button; status box variants `.status-active`, `.status-cutoff`,
`.status-saturation`; `.circuit-svg` sized to the card.

- [ ] **Step 7: Delete the old asset**

```bash
git rm static/circuit.svg
```

- [ ] **Step 8: Run the route tests**

Run: `.venv\Scripts\python.exe -m pytest tests/test_app.py -v`
Expected: all pass.

- [ ] **Step 9: Run the full suite**

Run: `.venv\Scripts\python.exe -m pytest -q`
Expected: all pass, no failures.

- [ ] **Step 10: Verify visually against the mockup**

Run the app, open `http://127.0.0.1:5000/`, compare side by side with the
mockup: header, three cards, unit selects, zigzag schematic with the entered
values, 2-decimal results, green active box. Then submit `2.2 kΩ` and
`2200 Ω` and confirm identical results, and check a narrow viewport stacks
cleanly.

- [ ] **Step 11: Commit**

```bash
git add app.py templates static tests/test_app.py
git commit -m "feat: restyle the bias page and add unit selects"
```
