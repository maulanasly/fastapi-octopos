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


def test_indonesia_preset_applies_id_number_format(client, manager_headers):
    """Selecting IDR/ID auto-applies the id_ID number format."""
    resp = client.put(
        "/api/v1/localization/",
        headers=manager_headers,
        json={"currency": "IDR", "country_code": "ID"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["number_format"] == "id_ID"


def test_explicit_number_format_not_overridden(client, manager_headers):
    """An explicit number_format in the payload wins over the ID preset."""
    resp = client.put(
        "/api/v1/localization/",
        headers=manager_headers,
        json={
            "currency": "IDR",
            "country_code": "ID",
            "number_format": "en_US",
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["number_format"] == "en_US"


def test_non_indonesia_currency_keeps_number_format(client, manager_headers):
    resp = client.put(
        "/api/v1/localization/",
        headers=manager_headers,
        json={"currency": "USD", "country_code": "US"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["number_format"] == "en_US"


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


def test_regions_endpoint_lists_presets(client, cashier_headers):
    resp = client.get("/api/v1/localization/regions", headers=cashier_headers)
    assert resp.status_code == 200, resp.text
    codes = {region["country_code"] for region in resp.json()}
    assert {"US", "ID"} <= codes
    by_code = {r["country_code"]: r for r in resp.json()}
    assert by_code["ID"]["currency"] == "IDR"
    assert by_code["ID"]["number_format"] == "id_ID"
    assert by_code["ID"]["timezone"] == "Asia/Jakarta"


def test_options_endpoint_lists_supported_values(client, manager_headers):
    resp = client.get("/api/v1/localization/options", headers=manager_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["languages"] == ["en", "id"]
    assert body["currencies"] == [
        "USD",
        "IDR",
        "EUR",
        "GBP",
        "SGD",
        "JPY",
        "MYR",
        "AUD",
    ]
    assert body["number_formats"] == ["en_US", "id_ID"]
    assert body["country_codes"] == ["US", "ID"]
    assert "Asia/Jakarta" in body["timezones"]
    assert "%d-%m-%Y %H:%M" in body["date_formats"]


def test_options_endpoint_requires_settings_manage(client, cashier_headers):
    resp = client.get("/api/v1/localization/options", headers=cashier_headers)
    assert resp.status_code == 403


def test_me_uses_global_default_when_no_region(client, cashier_headers):
    resp = client.get("/api/v1/localization/me", headers=cashier_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["language"] == "en"
    assert body["currency"] == "USD"


def test_set_and_clear_user_region(client, auth_factory):
    headers = auth_factory.user("region-user@example.com")

    resp = client.put("/api/v1/localization/me", headers=headers, json={"region": "ID"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["country_code"] == "ID"
    assert body["currency"] == "IDR"
    assert body["number_format"] == "id_ID"
    assert body["language"] == "id"
    assert body["timezone"] == "Asia/Jakarta"

    # persists across fetches
    resp = client.get("/api/v1/localization/me", headers=headers)
    assert resp.json()["currency"] == "IDR"

    # reset to global default
    resp = client.put("/api/v1/localization/me", headers=headers, json={"region": None})
    assert resp.status_code == 200, resp.text
    assert resp.json()["country_code"] == "US"
    assert resp.json()["currency"] == "USD"


def test_invalid_region_rejected(client, cashier_headers):
    resp = client.put(
        "/api/v1/localization/me", headers=cashier_headers, json={"region": "XX"}
    )
    assert resp.status_code == 422, resp.text


def test_regions_are_per_user(client, auth_factory):
    id_user = auth_factory.user("region-id@example.com")
    us_user = auth_factory.user("region-us@example.com")

    client.put("/api/v1/localization/me", headers=id_user, json={"region": "ID"})

    resp_us = client.get("/api/v1/localization/me", headers=us_user)
    resp_id = client.get("/api/v1/localization/me", headers=id_user)
    assert resp_us.json()["currency"] == "USD"
    assert resp_id.json()["currency"] == "IDR"


def test_format_currency_idr_has_space(client, cashier_headers):
    """The Indonesian convention places a space between Rp and the amount."""
    from app.core.localization import format_currency

    assert format_currency(4500.0, "IDR", "id_ID") == "Rp 4.500"
    assert format_currency(4500.0, "USD", "en_US") == "$4,500.00"
