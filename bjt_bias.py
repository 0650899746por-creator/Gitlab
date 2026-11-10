import math
from collections.abc import Mapping

REQUIRED_FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")

LABELS = {
    "vcc": "VCC",
    "r1": "R1",
    "r2": "R2",
    "rc": "RC",
    "re": "RE",
    "beta": "beta",
    "vbe": "VBE",
}

UNITS = {
    "vcc": ("V",),
    "r1": ("Ω", "kΩ"),
    "r2": ("Ω", "kΩ"),
    "rc": ("Ω", "kΩ"),
    "re": ("Ω", "kΩ"),
    "beta": ("",),
    "vbe": ("V",),
}

UNIT_FACTORS = {"V": 1.0, "Ω": 1.0, "kΩ": 1000.0, "": 1.0}

DEFAULT_UNITS = {
    "vcc": "V",
    "r1": "kΩ",
    "r2": "kΩ",
    "rc": "kΩ",
    "re": "kΩ",
    "beta": "",
    "vbe": "V",
}

VCE_SAT_V = 0.2
REL_TOL = 1e-9


def parse_inputs(
    raw: Mapping[str, str],
    units: Mapping[str, str] | None = None,
) -> tuple[dict[str, float] | None, list[str]]:
    """Parse and validate the seven bias inputs, collecting every error.

    ``units`` overrides ``DEFAULT_UNITS``; resistor values are converted to
    ohms and voltages stay in volts before validation.
    """
    resolved_units = {**DEFAULT_UNITS, **(units or {})}
    values: dict[str, float] = {}
    errors: list[str] = []

    for field in REQUIRED_FIELDS:
        label = LABELS[field]
        text = raw.get(field, "").strip()
        try:
            value = float(text)
        except (TypeError, ValueError):
            errors.append(f"{label} must be a number.")
            continue
        if not math.isfinite(value):
            errors.append(f"{label} must be a finite number.")
            continue
        unit = resolved_units[field]
        if unit not in UNITS[field]:
            errors.append(f"{label} unit is not supported.")
            continue
        values[field] = value * UNIT_FACTORS[unit]

    if "vcc" in values and values["vcc"] <= 0:
        errors.append("VCC must be greater than zero.")
    for field in ("r1", "r2", "rc", "re", "beta"):
        if field in values and values[field] <= 0:
            errors.append(f"{LABELS[field]} must be greater than zero.")
    if "vcc" in values and "vbe" in values:
        if not 0 <= values["vbe"] < values["vcc"]:
            errors.append("VBE must be between 0 and VCC.")

    if errors:
        return None, errors
    return values, []


def closed_form(
    vcc: float,
    r1: float,
    r2: float,
    rc: float,
    re: float,
    beta: float,
    vbe: float,
) -> dict[str, float]:
    """Solve the bias point with the Thevenin equivalent of the base divider."""
    vbb = vcc / (1.0 + r1 / r2)
    rb = 1.0 / (1.0 / r1 + 1.0 / r2)
    ib = (vbb - vbe) / (rb + (beta + 1) * re)
    if ib <= 0:
        return {
            "ib_a": 0.0,
            "ic_a": 0.0,
            "ie_a": 0.0,
            "vb_v": vbb,
            "ve_v": 0.0,
            "vc_v": vcc,
            "vce_v": vcc,
            "vbb_v": vbb,
            "rb_ohm": rb,
        }
    ic = beta * ib
    ie = (beta + 1) * ib
    ve = ie * re
    vb = ve + vbe
    vc = vcc - ic * rc
    return {
        "ib_a": ib,
        "ic_a": ic,
        "ie_a": ie,
        "vb_v": vb,
        "ve_v": ve,
        "vc_v": vc,
        "vce_v": vc - ve,
        "vbb_v": vbb,
        "rb_ohm": rb,
    }


def _solve_3x3(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    """Solve a 3x3 linear system by Gaussian elimination with partial pivoting."""
    augmented = [row[:] + [value] for row, value in zip(matrix, rhs)]
    for col in range(3):
        pivot = max(range(col, 3), key=lambda row: abs(augmented[row][col]))
        if pivot != col:
            augmented[col], augmented[pivot] = augmented[pivot], augmented[col]
        for row in range(col + 1, 3):
            factor = augmented[row][col] / augmented[col][col]
            for k in range(col, 4):
                augmented[row][k] -= factor * augmented[col][k]

    solution = [0.0, 0.0, 0.0]
    for row in (2, 1, 0):
        known = sum(augmented[row][col] * solution[col] for col in range(row + 1, 3))
        solution[row] = (augmented[row][3] - known) / augmented[row][row]
    return solution


def nodal(
    vcc: float,
    r1: float,
    r2: float,
    rc: float,
    re: float,
    beta: float,
    vbe: float,
) -> dict[str, float]:
    """Solve the same bias point from the 3-node system, without Thevenin."""
    vbb = vcc / (1.0 + r1 / r2)
    rb = 1.0 / (1.0 / r1 + 1.0 / r2)
    matrix = [
        [1.0, -1.0, 0.0],
        [-1.0 / r1 - 1.0 / r2, 0.0, -1.0],
        [0.0, -1.0 / re, beta + 1.0],
    ]
    rhs = [vbe, -vcc / r1, 0.0]
    _vb, _ve, ib = _solve_3x3(matrix, rhs)
    if ib <= 0:
        return {
            "ib_a": 0.0,
            "ic_a": 0.0,
            "ie_a": 0.0,
            "vb_v": vbb,
            "ve_v": 0.0,
            "vc_v": vcc,
            "vce_v": vcc,
            "vbb_v": vbb,
            "rb_ohm": rb,
        }
    ic = beta * ib
    ie = (beta + 1) * ib
    vc = vcc - ic * rc
    return {
        "ib_a": ib,
        "ic_a": ic,
        "ie_a": ie,
        "vb_v": _vb,
        "ve_v": _ve,
        "vc_v": vc,
        "vce_v": vc - _ve,
        "vbb_v": vbb,
        "rb_ohm": rb,
    }


def to_display(values: dict[str, float]) -> dict[str, str]:
    """Format the seven reported quantities with two decimals."""
    return {
        "ib_ua": f"{values['ib_a'] * 1e6:.2f}",
        "ic_ma": f"{values['ic_a'] * 1e3:.2f}",
        "ie_ma": f"{values['ie_a'] * 1e3:.2f}",
        "vb_v": f"{values['vb_v']:.2f}",
        "ve_v": f"{values['ve_v']:.2f}",
        "vc_v": f"{values['vc_v']:.2f}",
        "vce_v": f"{values['vce_v']:.2f}",
    }


def analyze(
    vcc: float,
    r1: float,
    r2: float,
    rc: float,
    re: float,
    beta: float,
    vbe: float,
) -> dict:
    """Compute the bias point with both solvers and report the operating region."""
    expected = closed_form(vcc, r1, r2, rc, re, beta, vbe)
    actual = nodal(vcc, r1, r2, rc, re, beta, vbe)
    if not all(math.isfinite(value) for value in expected.values()) or not all(
        math.isfinite(value) for value in actual.values()
    ):
        raise ValueError("Inputs are too large: the bias calculation overflowed.")
    max_abs_diff = max(abs(expected[key] - actual[key]) for key in expected)
    passed = all(
        abs(expected[key] - actual[key])
        <= REL_TOL * max(1.0, abs(expected[key]), abs(actual[key]))
        for key in expected
    )

    values = expected
    display = to_display(values)
    if values["vbb_v"] <= vbe:
        region = "cutoff"
        region_label = "Cut-off region"
        region_title = "Cut-off region"
        region_detail = (
            f"VBB = {values['vbb_v']:.2f} V ≤ VBE = {vbe:.2f} V "
            "(cut-off: no collector current)"
        )
        warnings = ["Transistor is cut off (VBB <= VBE): IB = IC = IE = 0."]
    elif values["vce_v"] < VCE_SAT_V:
        region = "saturation"
        region_label = "Saturation region"
        region_title = "Saturation region"
        region_detail = (
            f"VCE = {display['vce_v']} V < 0.2 V (saturation: fixed-beta model not valid)"
        )
        warnings = [
            "Transistor is in saturation (VCE < 0.2 V); "
            "the fixed-beta model is not valid."
        ]
    else:
        region = "active"
        region_label = "Active region"
        region_title = "Active region approximation OK"
        region_detail = (
            f"VCE = {display['vce_v']} V > 0.2 V (transistor in active region)"
        )
        warnings = []

    return {
        "values": values,
        "display": display,
        "region": region,
        "region_label": region_label,
        "region_title": region_title,
        "region_detail": region_detail,
        "warnings": warnings,
        "verification": {
            "closed_form": expected,
            "nodal": actual,
            "max_abs_diff": max_abs_diff,
            "passed": passed,
        },
    }
