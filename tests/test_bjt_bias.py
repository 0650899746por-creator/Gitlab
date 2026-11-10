import pytest

import math

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


from bjt_bias import closed_form, nodal


def test_closed_form_known_values():
    result = closed_form(12, 47000, 10000, 2200, 470, 150, 0.7)
    assert result["ib_a"] == pytest.approx(1.77397243587898e-05, rel=1e-9)
    assert result["ic_a"] == pytest.approx(0.0026609586538184696, rel=1e-9)
    assert result["ie_a"] == pytest.approx(0.0026786983781772597, rel=1e-9)
    assert result["ve_v"] == pytest.approx(1.2589882377433121, rel=1e-9)
    assert result["vb_v"] == pytest.approx(1.958988237743312, rel=1e-9)
    assert result["vc_v"] == pytest.approx(6.145890961599367, rel=1e-9)
    assert result["vce_v"] == pytest.approx(4.886902723856055, rel=1e-9)
    assert result["vbb_v"] == pytest.approx(2.1052631578947367, rel=1e-9)
    assert result["rb_ohm"] == pytest.approx(8245.61403508772, rel=1e-9)


def test_closed_form_cutoff_returns_zero_currents():
    result = closed_form(12, 47000, 1000, 2200, 470, 150, 0.7)
    assert result["ib_a"] == 0
    assert result["ic_a"] == 0
    assert result["ie_a"] == 0
    assert result["vb_v"] == pytest.approx(0.25)
    assert result["vc_v"] == 12
    assert result["vce_v"] == 12


def test_nodal_matches_closed_form():
    cases = [
        (12, 47000, 10000, 2200, 470, 150, 0.7),
        (5, 10000, 2200, 1000, 100, 100, 0.65),
        (15, 68000, 12000, 3300, 680, 200, 0.7),
        (9, 22000, 4700, 1500, 330, 80, 0.6),
        (24, 100000, 15000, 4700, 1000, 300, 0.7),
    ]
    for case in cases:
        expected = closed_form(*case)
        actual = nodal(*case)
        for key in expected:
            scale = max(1.0, abs(expected[key]), abs(actual[key]))
            assert abs(expected[key] - actual[key]) <= 1e-9 * scale, key


def test_nodal_cutoff_matches_closed_form():
    result = nodal(12, 47000, 1000, 2200, 470, 150, 0.7)
    assert result["ic_a"] == 0
    assert result["vb_v"] == pytest.approx(0.25)


from bjt_bias import analyze


def test_analyze_example_active_and_verification_passes():
    result = analyze(12, 47000, 10000, 2200, 470, 150, 0.7)
    assert result["region"] == "active"
    assert result["region_label"] == "Active region"
    assert result["warnings"] == []
    assert result["verification"]["passed"] is True
    assert result["verification"]["max_abs_diff"] <= 1e-9
    assert result["display"]["ib_ua"] == "17.740"
    assert result["display"]["ic_ma"] == "2.661"
    assert result["display"]["ie_ma"] == "2.679"
    assert result["display"]["vb_v"] == "1.959"
    assert result["display"]["ve_v"] == "1.259"
    assert result["display"]["vc_v"] == "6.146"
    assert result["display"]["vce_v"] == "4.887"
    assert result["display"]["vbb_v"] == "2.105"
    assert result["display"]["rb_ohm"] == "8245.614"


def test_analyze_cutoff_region_and_warning():
    result = analyze(12, 47000, 1000, 2200, 470, 150, 0.7)
    assert result["region"] == "cutoff"
    assert result["region_label"] == "Cut-off region"
    assert any("cut off" in warning.lower() for warning in result["warnings"])
    assert result["display"]["ic_ma"] == "0.000"


def test_analyze_saturation_region_and_warning():
    result = analyze(12, 47000, 10000, 4700, 470, 150, 0.7)
    assert result["region"] == "saturation"
    assert result["region_label"] == "Saturation region"
    assert any("saturation" in warning.lower() for warning in result["warnings"])
    assert result["display"]["vce_v"] == "-1.765"


def test_analyze_keeps_large_finite_inputs_finite():
    result = analyze(1e308, 47000, 10000, 2200, 470, 150, 0.7)
    assert all(math.isfinite(value) for value in result["values"].values())


def test_analyze_rejects_overflowing_result():
    with pytest.raises(ValueError, match="overflowed"):
        analyze(1e308, 1, 1e308, 2200, 1e-300, 150, 0.7)
