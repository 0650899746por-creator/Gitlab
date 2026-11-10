import pytest

import app as app_module

VALID_KILO = {
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1.0",
    "beta": "100",
    "vbe": "0.7",
    "unit_r1": "kΩ",
    "unit_r2": "kΩ",
    "unit_rc": "kΩ",
    "unit_re": "kΩ",
}

VALID_OHM = {
    "vcc": "12",
    "r1": "100000",
    "r2": "22000",
    "rc": "2200",
    "re": "1000",
    "beta": "100",
    "vbe": "0.7",
    "unit_r1": "Ω",
    "unit_r2": "Ω",
    "unit_rc": "Ω",
    "unit_re": "Ω",
}


@pytest.fixture()
def client():
    app_module.app.config.update(TESTING=True)
    return app_module.app.test_client()


def test_get_shows_all_inputs(client):
    html = client.get("/").get_data(as_text=True)
    for name in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"):
        assert f'name="{name}"' in html


def test_page_has_no_javascript(client):
    html = client.get("/").get_data(as_text=True)
    assert "<script" not in html.lower()


def test_page_has_unit_selects(client):
    html = client.get("/").get_data(as_text=True)
    for name in ("unit_r1", "unit_r2", "unit_rc", "unit_re"):
        assert f'name="{name}"' in html
    assert "kΩ" in html
    assert "Ω" in html


def test_kilo_ohm_and_ohm_post_give_same_result(client):
    kilos = client.post("/", data=VALID_KILO).get_data(as_text=True)
    ohms = client.post("/", data=VALID_OHM).get_data(as_text=True)
    for text in ("1.23", "8.05", "Active region approximation OK"):
        assert text in kilos
        assert text in ohms


def test_results_use_two_decimals(client):
    html = client.post("/", data=VALID_KILO).get_data(as_text=True)
    assert "1.23 mA" in html
    assert "8.05 V" in html
    assert "8.0523" not in html
    assert 'class="status status-active"' in html


def test_selected_unit_is_preserved(client):
    html = client.post("/", data={**VALID_OHM, "unit_r1": "Ω"}).get_data(as_text=True)
    assert '<option value="Ω" selected>' in html


def test_page_shows_live_circuit_values(client):
    html = client.post("/", data=VALID_KILO).get_data(as_text=True)
    assert 'class="circuit-svg"' in html
    assert "VCC = 12 V" in html
    assert "100 kΩ" in html
    assert "2.2 kΩ" in html
    assert "β = 100" in html


def test_page_hides_cross_check(client):
    html = client.post("/", data=VALID_KILO).get_data(as_text=True)
    assert "max |Δ|" not in html


def test_post_invalid_shows_error_without_results(client):
    response = client.post("/", data={**VALID_KILO, "vcc": "0"})
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "VCC must be greater than zero" in html
    assert "1.23 mA" not in html


def test_post_cutoff_shows_warning(client):
    response = client.post("/", data={**VALID_KILO, "r2": "1"})
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Cut-off region" in html
    assert 'class="status status-cutoff"' in html
    assert "no collector current" in html


def test_post_saturation_shows_warning(client):
    response = client.post("/", data={**VALID_KILO, "rc": "10"})
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Saturation region" in html
    assert 'class="status status-saturation"' in html
    assert "fixed-beta" in html


def test_post_overflow_shows_error_without_results(client):
    response = client.post(
        "/",
        data={**VALID_OHM, "vcc": "1e308", "r1": "1", "r2": "1e308", "re": "1e-300"},
    )
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "overflowed" in html
    assert "1.23 mA" not in html


def test_route_uses_backend_analyze(client, monkeypatch):
    captured = {}
    fake = {
        "values": {
            "ib_a": 0.0, "ic_a": 0.0, "ie_a": 0.0,
            "vb_v": 0.0, "ve_v": 0.0, "vc_v": 0.0, "vce_v": 0.0,
            "vbb_v": 0.0, "rb_ohm": 0.0,
        },
        "display": {
            "ib_ua": "1.00", "ic_ma": "999.99", "ie_ma": "1.00",
            "vb_v": "0.00", "ve_v": "0.00", "vc_v": "0.00", "vce_v": "0.00",
        },
        "region": "active",
        "region_label": "Active region",
        "region_title": "Active region approximation OK",
        "region_detail": "VCE = 0.00 V > 0.2 V (transistor in active region)",
        "warnings": [],
        "verification": {"closed_form": {}, "nodal": {}, "max_abs_diff": 0.0, "passed": True},
    }

    def fake_analyze(**kwargs):
        captured.update(kwargs)
        return fake

    monkeypatch.setattr(app_module.bjt_bias, "analyze", fake_analyze)
    html = client.post("/", data=VALID_KILO).get_data(as_text=True)
    assert "999.99" in html
    assert captured["vcc"] == 12.0
