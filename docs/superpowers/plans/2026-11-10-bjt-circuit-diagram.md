# BJT Circuit Diagram Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a static SVG schematic of the voltage-divider-biased NPN common-emitter stage to the lab page.

**Architecture:** One hand-authored SVG asset in `static/`, embedded by the existing server-rendered template above the form. No JavaScript, no request-time rendering, no change to the calculation path.

**Tech Stack:** SVG 1.1, Jinja2 template, Flask static serving, pytest.

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-circuit-diagram-design.md`

## Global Constraints

- Static asset only: no `<script>`, no interactivity, no per-request drawing.
- Labels must match the app's input names exactly: `VCC`, `R1`, `R2`, `RC`, `RE`, `beta`, `VBE`, plus `VCE`.
- Reuse the page palette: strokes `#1f2933`, accent `#2f6f9f`.
- The existing test suite must stay green (31 tests before this change).

## Review Focus

1. **Asset missing or mistyped** — a person expects the diagram to render, not a broken image icon.
2. **Wrong topology** — a person expects R1 and R2 to form the base divider and RC/RE to sit on collector/emitter; a swapped resistor teaches the wrong circuit.
3. **Missing labels** — a person expects every form input to appear on the diagram.
4. **Squashed or clipped drawing** — a person expects the whole schematic visible at narrow width.
5. **Accessibility** — a screen reader should get a name and description, not an unlabeled image.

---

### Task 1: Circuit SVG asset and figure on the page

**Files:**
- Create: `static/circuit.svg`
- Modify: `templates/index.html` (insert the figure above `<form>`)
- Modify: `static/style.css` (append `.circuit` rules)
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: the existing `index` route and `static` endpoint; no Python changes.
- Produces: `static/circuit.svg` served at `/static/circuit.svg` with type `image/svg+xml`; a `<figure class="circuit">` in the page.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_app.py`:

```python
def test_page_shows_circuit_figure(client):
    html = client.get("/").get_data(as_text=True)
    assert 'class="circuit"' in html
    assert "circuit.svg" in html


def test_circuit_asset_is_svg_with_labels(client):
    response = client.get("/static/circuit.svg")
    assert response.status_code == 200
    assert "image/svg+xml" in response.headers["Content-Type"]
    body = response.get_data(as_text=True)
    assert "<svg" in body
    for label in ("VCC", "R1", "R2", "RC", "RE", "VBE", "VCE", "beta"):
        assert label in body
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_app.py -k circuit -v`
Expected: both fail — no `circuit.svg` reference in the page and 404 for the asset.

- [ ] **Step 3: Create `static/circuit.svg`**

Hand-authored, `viewBox="0 0 480 420"`, no fixed `width`/`height`.
Required content: VCC rail at the top; `R1` from the rail to the base node;
`R2` from the base node to ground; `RC` from the rail to the collector;
`RE` from the emitter to ground; NPN symbol with the emitter arrow pointing
away from the base; node dot at the base junction; ground symbols under `R2`
and `RE`; text labels `VCC`, `R1`, `R2`, `RC`, `RE`, `VBE`, `VCE`, `Q1`,
`beta`. Include `role="img"`, `<title>`, and `<desc>`.

- [ ] **Step 4: Embed the figure in `templates/index.html`**

Insert immediately after the `.subtitle` paragraph and before `<form>`:

```html
<figure class="circuit">
  <img src="{{ url_for('static', filename='circuit.svg') }}"
       alt="Voltage-divider biased NPN common-emitter stage: R1 and R2 form the base divider, RC connects the collector to VCC, RE connects the emitter to ground.">
  <figcaption>Voltage-divider bias, NPN common emitter</figcaption>
</figure>
```

- [ ] **Step 5: Add the CSS**

Append to `static/style.css`:

```css
.circuit {
  margin: 0 0 1.25rem;
  padding: 1rem;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  text-align: center;
}

.circuit img {
  display: block;
  width: 100%;
  max-width: 420px;
  height: auto;
  margin: 0 auto;
}

.circuit figcaption {
  color: var(--muted);
  font-size: 0.9rem;
  margin-top: 0.5rem;
}
```

- [ ] **Step 6: Run the circuit tests**

Run: `.venv\Scripts\python.exe -m pytest tests/test_app.py -k circuit -v`
Expected: 2 passed.

- [ ] **Step 7: Run the full suite**

Run: `.venv\Scripts\python.exe -m pytest -q`
Expected: 33 passed.

- [ ] **Step 8: Verify visually**

Run the app, open `http://127.0.0.1:5000/`, confirm the schematic renders
above the form, all eight labels are readable, and nothing is clipped at a
narrow viewport.

- [ ] **Step 9: Commit**

```bash
git add static/circuit.svg templates/index.html static/style.css tests/test_app.py
git commit -m "feat: add circuit schematic to the bias page"
```
