import pytest

from bjt_bias import parse_inputs

VALID = {
    "vcc": "12",
    "r1": "47000",
    "r2": "10000",
    "rc": "2200",
    "re": "470",
    "beta": "150",
    "vbe": "0.7",
}


def test_parse_valid_returns_floats():
    values, errors = parse_inputs(VALID)
    assert errors == []
    assert values["vcc"] == 12.0
    assert values["beta"] == 150.0


def test_parse_rejects_non_numeric_and_missing():
    values, errors = parse_inputs({**VALID, "rc": "abc"})
    assert values is None
    assert any("RC" in error for error in errors)

    values, errors = parse_inputs({k: v for k, v in VALID.items() if k != "vbe"})
    assert values is None
    assert any("VBE" in error for error in errors)


@pytest.mark.parametrize(
    "field,value,label",
    [
        ("vcc", "0", "VCC"),
        ("r1", "0", "R1"),
        ("r2", "-1", "R2"),
        ("rc", "0", "RC"),
        ("re", "0", "RE"),
        ("beta", "0", "beta"),
        ("vbe", "12", "VBE"),
    ],
)
def test_parse_rejects_out_of_range(field, value, label):
    values, errors = parse_inputs({**VALID, field: value})
    assert values is None
    assert any(label in error for error in errors)


def test_parse_collects_all_errors():
    values, errors = parse_inputs({**VALID, "r1": "-1", "rc": "0", "beta": "0"})
    assert values is None
    assert len(errors) == 3


def test_parse_rejects_non_finite():
    values, errors = parse_inputs({**VALID, "r1": "1e400"})
    assert values is None
    assert any("finite" in error.lower() for error in errors)
