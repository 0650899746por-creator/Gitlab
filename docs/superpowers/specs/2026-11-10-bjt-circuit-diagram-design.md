# Circuit diagram figure — short design

**Date:** 2026-11-10
**Status:** approved (chat, 2026-11-10)
**Adds to:** `docs/superpowers/specs/2026-11-10-bjt-ce-bias-design.md`

## Intent

The lab page computes the bias point but never shows the circuit it is
computing. Add one static schematic so a reader can connect each input to
its component without leaving the page.

## Goals

- Show the voltage-divider-biased NPN common-emitter stage: VCC rail, R1
  (VCC→base), R2 (base→ground), RC (VCC→collector), RE (emitter→ground),
  Q1 NPN symbol, node dots.
- Label every quantity the app asks for: VCC, R1, R2, RC, RE, beta, VBE,
  plus VCE.
- Render above the input form as a captioned figure.
- Stay a static asset: no JavaScript, no interactivity, no calculation.

## Non-goals

- No AC model, small-signal equivalent, or load line plot.
- No per-request rendering, no parameter values drawn into the image.
- No second diagram, no FET, no circuit editor.

## Approaches considered

| Approach | Trade-off | Decision |
|---|---|---|
| Hand-authored SVG | Crisp at any zoom, sharp labels, ~3 KB, fully controllable | **Chosen** |
| Raster PNG from a generator | Easy to paste into Word, but labels and wire joins drift and are hard to correct | Rejected |
| ASCII/text schematic | Lightest, but not a real schematic | Rejected |

## Design

- `static/circuit.svg`: `viewBox` based, no fixed pixel size, strokes
  `#1f2933`, accent `#2f6f9f`, `role="img"` with `<title>` and `<desc>`.
- `templates/index.html`: a `<figure class="circuit">` above the form with
  `<img src="{{ url_for('static', filename='circuit.svg') }}" ...>` and a
  `<figcaption>` naming the topology.
- `static/style.css`: `.circuit` sizing only (`max-width`, centered,
  light panel background). No new color variables.
- Tests (`tests/test_app.py`): the page references `circuit.svg`, and a GET
  for the asset returns 200 with an SVG content type.

## Left to the builder

- Exact coordinates and wire routing.
- Whether the NPN symbol is a circle-enclosed arrow or a bare arrow.
- Font size and label offsets.
