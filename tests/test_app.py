import pytest

import app as app_module

VALID = {
    "vcc": "12",
    "r1": "47000",
    "r2": "10000",
    "rc": "2200",
    "re": "470",
    "beta": "150",
    "vbe": "0.7",
}


@pytest.fixture()
def client():
    app_module.app.config.update(TESTING=True)
    return app_module.app.test_client()


def test_get_shows_all_inputs(client):
    html = client.get("/").get_data(as_text=True)
    for name in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"):
        assert f'name="{name}"' in html


def test_post_valid_shows_computed_values(client):
    html = client.post("/", data=VALID).get_data(as_text=True)
    assert "17.740" in html
    assert "2.661" in html
    assert "4.887" in html
    assert "Active region" in html
    assert "PASS" in html


def test_post_invalid_shows_error_without_results(client):
    response = client.post("/", data={**VALID, "vcc": "0"})
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "VCC must be greater than zero" in html
    assert "Operating point" not in html


def test_post_cutoff_shows_warning(client):
    response = client.post("/", data={**VALID, "r2": "1000"})
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Cut-off region" in html
    assert "cut off" in html.lower()


def test_post_saturation_shows_warning(client):
    response = client.post("/", data={**VALID, "rc": "4700"})
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Saturation region" in html
    assert "saturation" in html.lower()


def test_post_overflow_shows_error_without_results(client):
    response = client.post(
        "/",
        data={**VALID, "vcc": "1e308", "r1": "1", "r2": "1e308", "re": "1e-300"},
    )
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "overflowed" in html
    assert "Operating point" not in html


def test_route_uses_backend_analyze(client, monkeypatch):
    captured = {}
    fake = {
        "values": {
            "ib_a": 0.0, "ic_a": 0.0, "ie_a": 0.0,
            "vb_v": 0.0, "ve_v": 0.0, "vc_v": 0.0, "vce_v": 0.0,
            "vbb_v": 0.0, "rb_ohm": 0.0,
        },
        "display": {
            "ib_ua": "1.000", "ic_ma": "999.999", "ie_ma": "1.000",
            "vb_v": "0.000", "ve_v": "0.000", "vc_v": "0.000",
            "vce_v": "0.000", "vbb_v": "0.000", "rb_ohm": "0.000",
        },
        "region": "active",
        "region_label": "Active region",
        "warnings": [],
        "verification": {"closed_form": {}, "nodal": {}, "max_abs_diff": 0.0, "passed": True},
    }

    def fake_analyze(**kwargs):
        captured.update(kwargs)
        return fake

    monkeypatch.setattr(app_module.bjt_bias, "analyze", fake_analyze)
    html = client.post("/", data=VALID).get_data(as_text=True)
    assert "999.999" in html
    assert captured["vcc"] == 12.0


def test_page_has_no_javascript(client):
    html = client.get("/").get_data(as_text=True)
    assert "<script" not in html.lower()


def test_page_shows_circuit_figure(client):
    html = client.get("/").get_data(as_text=True)
    assert 'class="circuit"' in html
    assert "circuit.svg" in html


def test_circuit_asset_is_svg_with_labels(client):
    response = client.get("/static/circuit.svg")
    assert response.status_code == 200
    assert "image/svg+xml" in response.headers["Content-Type"]
    body = response.get_data(as_text=True)
    assert "<svg" in body
    for label in ("VCC", "R1", "R2", "RC", "RE", "VBE", "VCE", "beta"):
        assert label in body
