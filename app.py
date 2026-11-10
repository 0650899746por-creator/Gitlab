import bjt_bias
from flask import Flask, render_template, request

DEFAULT_FORM = {
    "vcc": "12",
    "r1": "47000",
    "r2": "10000",
    "rc": "2200",
    "re": "470",
    "beta": "150",
    "vbe": "0.7",
}


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/", methods=["GET", "POST"])
    def index():
        form = dict(DEFAULT_FORM)
        errors: list[str] = []
        result = None

        if request.method == "POST":
            for field in bjt_bias.REQUIRED_FIELDS:
                form[field] = request.form.get(field, "")
            values, errors = bjt_bias.parse_inputs(request.form)
            if values is not None:
                result = bjt_bias.analyze(**values)

        return render_template("index.html", form=form, errors=errors, result=result)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
