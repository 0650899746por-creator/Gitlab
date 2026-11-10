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


def parse_inputs(raw: Mapping[str, str]) -> tuple[dict[str, float] | None, list[str]]:
    """Parse and validate the seven bias inputs, collecting every error."""
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
        values[field] = value

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
    vbb = vcc * r2 / (r1 + r2)
    rb = r1 * r2 / (r1 + r2)
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
    vbb = vcc * r2 / (r1 + r2)
    rb = r1 * r2 / (r1 + r2)
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
