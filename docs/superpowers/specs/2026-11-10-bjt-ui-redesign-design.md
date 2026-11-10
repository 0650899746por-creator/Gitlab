# UI redesign and resistor units — design

**Date:** 2026-11-10
**Status:** awaiting approval
**Supersedes (UI only):** `2026-11-10-bjt-ce-bias-design.md`

## Intent

The page works but does not look like the lab handout mockup, and the
resistor fields force the student to type ohms. Make the page match the
mockup and let each resistor be entered in Ω or kΩ.

## Goals

- Three-card layout: Input Parameters | Circuit | DC Bias Results, with the
  header (chip icon, "Lab 02: BJT DC Bias Web App", subtitle, course badge).
- Per-field unit select: `V` for VCC and VBE, `Ω`/`kΩ` for R1, R2, RC, RE,
  and `–` for beta. Selection is preserved after submit.
- The circuit diagram shows the entered values (`R1 100 kΩ`, `VCC = 12 V`,
  `β = 100`, …) and uses the mockup's circled-NPN look.
- All displayed results use 2 decimal places with units.
- Region status becomes one coloured box: green active, amber cut-off, red
  saturation, each with a computed detail line.

## Non-goals

- No JavaScript, no client-side calculation, no live update while typing.
- No AC/Bode/transient, no FET, no circuit editor.
- No change to the solvers or to the cross-check logic (it stays in the
  backend; it is just no longer shown).

## Approaches

| Approach | Trade-off | Decision |
|---|---|---|
| Inline SVG via `{% include %}` with Jinja values | Values update with the form; no extra request; testable in the HTML | **Chosen** |
| `/circuit.svg?r1=…` route | Cacheable asset, but needs a second render path and URL plumbing | Rejected |
| Static SVG + HTML value overlay | Keeps the old asset, but labels drift from the drawing | Rejected |

## Design

### Units

- `UNITS` maps each field to its allowed units; `UNIT_FACTORS` maps `Ω → 1`,
  `kΩ → 1000`, `V → 1`.
- `parse_inputs(raw, units=None)` reads `unit_<field>`, converts to base
  units (Ω, V), then validates exactly as today. An unknown unit is an error.
- `DEFAULT_UNITS` keeps resistors in `kΩ`.

### Display

- `to_display` returns the seven shown quantities at 2 decimals:
  `ib_ua, ic_ma, ie_ma, vb_v, ve_v, vc_v, vce_v`.
- `VBB`/`RB` stay in `values` (hand calculation) but leave the results table.
- `analyze` gains `region_detail` — a sentence built from the computed
  numbers (e.g. `VCE = 7.20 V > 0.2 V (transistor in active region)`).

### Page

- `templates/index.html`: header, three cards, input rows (label + number +
  unit select), results table, status box, error list.
- `templates/_circuit.svg`: inline SVG included by the page; takes a
  `circuit` dict of preformatted strings from the route.
- `static/style.css`: rewritten for the mockup palette (light blue-grey page,
  white cards, teal `#0f7b8a` accent).
- `static/circuit.svg` and its asset test are removed.

### Defaults

`VCC 12`, `R1 100 kΩ`, `R2 22 kΩ`, `RC 2.2 kΩ`, `RE 1.0 kΩ`, `beta 100`,
`VBE 0.70` — the mockup's values, so the first load looks like the picture.
The computed result will differ from the mockup's numbers because the mockup
used the approximate method and ignored base-current loading; this app solves
exactly.

## Left to the builder

- Exact icon paths, spacing, and type scale.
- Whether the unit select shows a dash or is disabled for beta.
