import bjt_bias
from flask import Flask, render_template, request

DEFAULT_FORM = {
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1.0",
    "rb": "1000",
    "beta": "100",
    "vbe": "0.7",
}

FIELDS = (
    ("vcc", "V<sub>CC</sub> (Supply Voltage)", "V"),
    ("r1", "R<sub>1</sub> (Upper Divider)", "R"),
    ("r2", "R<sub>2</sub> (Lower Divider)", "R"),
    ("rc", "R<sub>C</sub> (Collector Resistor)", "R"),
    ("re", "R<sub>E</sub> (Emitter Resistor)", "R"),
    ("rb", "R<sub>B</sub> (Base Resistor)", "R"),
    ("beta", "β (Current Gain)", ""),
    ("vbe", "V<sub>BE</sub> (Base–Emitter Voltage)", "V"),
)

MODE_DESCRIPTIONS = {
    "divider": "R₁ · R₂ · R_E — เสถียรเมื่อ β เปลี่ยน",
    "fixed": "R_B — วงจรง่าย แต่จุดทำงานไวต่อ β",
    "emitter": "R_B · R_E · แหล่งจ่ายเดียว — มี negative feedback ที่ R_E",
}

MODE_FORMULAS = {
    "fixed": "I_B = (V_CC − V_BE) / R_B",
    "emitter": "I_B = (V_CC − V_BE) / [R_B + (β+1)R_E]",
    "divider": "I_B = (V_TH − V_BE) / [R_TH + (β+1)R_E]",
}


def _quantity(text: str, unit: str) -> str:
    """Render an entered value with its unit, trimming trailing zeros."""
    try:
        number = float(text)
    except (TypeError, ValueError):
        return f"{text} {unit}".strip()
    return f"{number:g} {unit}".strip()


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/", methods=["GET", "POST"])
    def index():
        mode = request.values.get("mode", "divider")
        if mode not in bjt_bias.MODES:
            mode = "divider"

        form = dict(DEFAULT_FORM)
        units = dict(bjt_bias.DEFAULT_UNITS)
        errors: list[str] = []
        result = None
        gauges = None

        if request.method == "POST":
            posted_mode = request.form.get("mode", mode)
            if posted_mode in bjt_bias.MODES:
                mode = posted_mode
            for field in ("vcc", "r1", "r2", "rc", "re", "rb", "beta", "vbe"):
                if field in form:
                    form[field] = request.form.get(field, form[field])
            for field in ("vcc", "r1", "r2", "rc", "re", "rb", "beta", "vbe"):
                key = f"unit_{field}"
                if key in request.form:
                    units[field] = request.form.get(key, units.get(field, bjt_bias.DEFAULT_UNITS.get(field, "")))

        values, errors = bjt_bias.parse_inputs(form, units, mode=mode)
        if values is not None:
            try:
                result = bjt_bias.analyze_mode(mode, values)
            except ValueError as error:
                errors.append(str(error))

        if result is not None:
            vcc = values["vcc"]
            rc = values["rc"]
            ic_sat = vcc / rc * 1e3
            vce = result["values"]["vce_v"]
            ic = result["values"]["ic_a"] * 1e3
            gauges = {
                "vce_pct": max(0.0, min(100.0, vce / vcc * 100.0)),
                "ic_pct": max(0.0, min(100.0, ic / ic_sat * 100.0)),
                "ic_sat_ma": ic_sat,
                "vcc_v": vcc,
            }

        circuit = {
            "vcc": _quantity(form.get("vcc", ""), units.get("vcc", "V")),
            "r1": _quantity(form.get("r1", ""), units.get("r1", "kΩ")),
            "r2": _quantity(form.get("r2", ""), units.get("r2", "kΩ")),
            "rc": _quantity(form.get("rc", ""), units.get("rc", "kΩ")),
            "re": _quantity(form.get("re", ""), units.get("re", "kΩ")),
            "beta": _quantity(form.get("beta", ""), ""),
        }

        return render_template(
            "index.html",
            mode=mode,
            mode_label=bjt_bias.MODE_LABELS[mode],
            mode_options=[
                {"key": key, "label": bjt_bias.MODE_LABELS[key], "desc": MODE_DESCRIPTIONS[key]}
                for key in bjt_bias.MODES
            ],
            form=form,
            units=units,
            fields=FIELDS,
            errors=errors,
            result=result,
            circuit=circuit,
            gauges=gauges,
            formula=MODE_FORMULAS[mode],
        )

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
