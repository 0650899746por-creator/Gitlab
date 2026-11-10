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
