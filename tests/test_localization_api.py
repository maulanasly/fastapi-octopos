"""Integration tests for the localization API."""


def test_get_default_localization_settings(client, cashier_headers):
    resp = client.get("/api/v1/localization/", headers=cashier_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["language"] == "en"
    assert body["currency"] == "USD"
    assert body["timezone"] == "UTC"


def test_manager_can_update_currency(client, manager_headers):
    resp = client.put(
        "/api/v1/localization/",
        headers=manager_headers,
        json={"currency": "IDR", "country_code": "ID"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["currency"] == "IDR"
    assert resp.json()["country_code"] == "ID"


def test_cashier_cannot_update_settings(client, cashier_headers):
    resp = client.put(
        "/api/v1/localization/",
        headers=cashier_headers,
        json={"currency": "EUR"},
    )
    assert resp.status_code == 403


def test_updated_settings_persist(client, manager_headers, cashier_headers):
    client.put(
        "/api/v1/localization/",
        headers=manager_headers,
        json={"language": "id"},
    )
    resp = client.get("/api/v1/localization/", headers=cashier_headers)
    assert resp.json()["language"] == "id"
