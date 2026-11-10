import bjt_bias
from flask import Flask, render_template, request

DEFAULT_FORM = {
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1.0",
    "beta": "100",
    "vbe": "0.7",
}

FIELDS = (
    ("vcc", "V<sub>CC</sub> (Supply Voltage)", "V"),
    ("r1", "R<sub>1</sub> (Upper Divider)", "R"),
    ("r2", "R<sub>2</sub> (Lower Divider)", "R"),
    ("rc", "R<sub>C</sub> (Collector Resistor)", "R"),
    ("re", "R<sub>E</sub> (Emitter Resistor)", "R"),
    ("beta", "β (Current Gain)", ""),
    ("vbe", "V<sub>BE</sub> (Base–Emitter Voltage)", "V"),
)


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
        form = dict(DEFAULT_FORM)
        units = dict(bjt_bias.DEFAULT_UNITS)
        errors: list[str] = []
        result = None

        if request.method == "POST":
            for field in bjt_bias.REQUIRED_FIELDS:
                form[field] = request.form.get(field, "")
                units[field] = request.form.get(
                    f"unit_{field}", bjt_bias.DEFAULT_UNITS[field]
                )

        values, errors = bjt_bias.parse_inputs(form, units)
        if values is not None:
            try:
                result = bjt_bias.analyze(**values)
            except ValueError as error:
                errors.append(str(error))

        circuit = {
            field: _quantity(form[field], units[field])
            for field in ("vcc", "r1", "r2", "rc", "re", "beta")
        }

        return render_template(
            "index.html",
            form=form,
            units=units,
            fields=FIELDS,
            errors=errors,
            result=result,
            circuit=circuit,
        )

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
