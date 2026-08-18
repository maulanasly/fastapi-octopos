"""Order tracking API: destination-aware service trips, location pings,
geo queries, permissions, SSE events, and offline sync replay."""

import json

import _tenant_mode
import pytest
from conftest import order_payload
from sqlalchemy import text


def _tracked_order(client, headers, product_id, lat=6.2, lng=106.8):
    payload = order_payload(product_id, quantity=1)
    payload["destination_address"] = "Jl. Sudirman No. 1"
    payload["destination_lat"] = lat
    payload["destination_lng"] = lng
    resp = client.post("/api/v1/orders/", headers=headers, json=payload)
    assert resp.status_code == 200, resp.text
    order = resp.json()
    assert order["destination_address"] == "Jl. Sudirman No. 1"
    assert order["destination_lat"] == lat
    assert order["tracking_status"] == "none"
    total = order["total_amount"]
    resp = client.post(
        f"/api/v1/orders/{order['id']}/payments",
        headers=headers,
        json={"payment_method": "cash", "amount": total},
    )
    assert resp.status_code == 200, resp.text
    return order


def _assign(client, headers, order_id):
    resp = client.post(
        f"/api/v1/orders/tracking/{order_id}/status",
        headers=headers,
        json={"status": "assigned"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


class TestStateMachine:
    def test_full_trip_assigned_en_route_on_site(
        self, client, cashier_headers, manager_headers, make_product, open_drawer
    ):
        product = make_product(manager_headers, name="Wash", sku="SKU-WASH")
        open_drawer(cashier_headers)
        order = _tracked_order(client, cashier_headers, product["id"])
        order_id = order["id"]

        order = _assign(client, manager_headers, order_id)
        assert order["tracking_status"] == "assigned"
        assert order["assigned_at"] is not None

        resp = client.post(
            f"/api/v1/orders/tracking/{order_id}/status",
            headers=manager_headers,
            json={"status": "en_route"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["tracking_status"] == "en_route"
        assert resp.json()["en_route_at"] is not None

        resp = client.post(
            f"/api/v1/orders/tracking/{order_id}/status",
            headers=manager_headers,
            json={"status": "on_site"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["tracking_status"] == "on_site"

    def test_cannot_skip_states(
        self, client, cashier_headers, manager_headers, make_product, open_drawer
    ):
        product = make_product(manager_headers, name="Skip", sku="SKU-SKIP")
        open_drawer(cashier_headers)
        order = _tracked_order(client, cashier_headers, product["id"])

        resp = client.post(
            f"/api/v1/orders/tracking/{order['id']}/status",
            headers=manager_headers,
            json={"status": "en_route"},
        )
        assert resp.status_code == 400, resp.text

    def test_cannot_assign_without_destination(
        self, client, cashier_headers, manager_headers, make_product, open_drawer
    ):
        product = make_product(manager_headers, name="NoDest", sku="SKU-NOD")
        open_drawer(cashier_headers)
        order = client.post(
            "/api/v1/orders/",
            headers=cashier_headers,
            json=order_payload(product["id"]),
        ).json()
        total = order["total_amount"]
        client.post(
            f"/api/v1/orders/{order['id']}/payments",
            headers=cashier_headers,
            json={"payment_method": "cash", "amount": total},
        )
        resp = client.post(
            f"/api/v1/orders/tracking/{order['id']}/status",
            headers=manager_headers,
            json={"status": "assigned"},
        )
        assert resp.status_code == 400, resp.text

    def test_cannot_track_unpaid_order(
        self, client, cashier_headers, manager_headers, make_product, open_drawer
    ):
        product = make_product(manager_headers, name="Unpaid", sku="SKU-UNP")
        open_drawer(cashier_headers)
        order = client.post(
            "/api/v1/orders/",
            headers=cashier_headers,
            json={
                "items": [{"product_id": product["id"], "quantity": 1}],
                "destination_address": "Jl. A",
                "destination_lat": 6.2,
                "destination_lng": 106.8,
            },
        ).json()
        resp = client.post(
            f"/api/v1/orders/tracking/{order['id']}/status",
            headers=manager_headers,
            json={"status": "assigned"},
        )
        assert resp.status_code == 400, resp.text

    def test_invalid_status_rejected(
        self, client, cashier_headers, manager_headers, make_product, open_drawer
    ):
        product = make_product(manager_headers, name="Bad", sku="SKU-BAD")
        open_drawer(cashier_headers)
        order = _tracked_order(client, cashier_headers, product["id"])
        resp = client.post(
            f"/api/v1/orders/tracking/{order['id']}/status",
            headers=manager_headers,
            json={"status": "teleported"},
        )
        assert resp.status_code == 400, resp.text


class TestLocations:
    def test_report_location_appends_and_updates_latest(
        self, client, cashier_headers, manager_headers, make_product, open_drawer
    ):
        product = make_product(manager_headers, name="Loc", sku="SKU-LOC")
        open_drawer(cashier_headers)
        order = _tracked_order(client, cashier_headers, product["id"])
        _assign(client, manager_headers, order["id"])

        for lat, lng in ((6.21, 106.81), (6.22, 106.82)):
            resp = client.post(
                f"/api/v1/orders/tracking/{order['id']}/location",
                headers=manager_headers,
                json={"lat": lat, "lng": lng, "source": "gps"},
            )
            assert resp.status_code == 200, resp.text
            assert resp.json()["lat"] == lat
            assert resp.json()["source"] == "gps"

        active = client.get("/api/v1/orders/tracking/", headers=manager_headers).json()
        assert len(active) == 1
        assert active[0]["latest_location"]["lat"] == 6.22
        assert active[0]["latest_location"]["lng"] == 106.82

        detail = client.get("/api/v1/orders/", headers=cashier_headers).json()
        tracked = [o for o in detail if o["id"] == order["id"]][0]
        assert tracked["latest_location"]["lat"] == 6.22

    def test_location_rejected_for_untracked_order(
        self, client, cashier_headers, manager_headers, make_product, open_drawer
    ):
        product = make_product(manager_headers, name="NotTr", sku="SKU-NTR")
        open_drawer(cashier_headers)
        order = _tracked_order(client, cashier_headers, product["id"])
        resp = client.post(
            f"/api/v1/orders/tracking/{order['id']}/location",
            headers=manager_headers,
            json={"lat": 6.2, "lng": 106.8},
        )
        assert resp.status_code == 400, resp.text


class TestGeoQueries:
    def test_nearest_orders_radius_and_order(
        self, client, cashier_headers, manager_headers, make_product, open_drawer
    ):
        product = make_product(manager_headers, name="Near", sku="SKU-NEAR")
        open_drawer(cashier_headers)
        # ~0.55km apart at these coordinates
        near = _tracked_order(
            client, cashier_headers, product["id"], lat=6.21, lng=106.81
        )
        far = _tracked_order(
            client, cashier_headers, product["id"], lat=6.219, lng=106.812
        )
        _assign(client, manager_headers, near["id"])
        _assign(client, manager_headers, far["id"])

        resp = client.get(
            "/api/v1/orders/tracking/nearest",
            headers=manager_headers,
            params={"lat": 6.21, "lng": 106.81, "radius_km": 2},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert [o["order_id"] for o in body] == [near["id"], far["id"]]
        assert body[0]["distance_m"] < body[1]["distance_m"]
        assert body[0]["destination_address"] == "Jl. Sudirman No. 1"

        # Tight radius excludes the far order.
        resp = client.get(
            "/api/v1/orders/tracking/nearest",
            headers=manager_headers,
            params={"lat": 6.21, "lng": 106.81, "radius_km": 0.5},
        )
        assert [o["order_id"] for o in resp.json()] == [near["id"]]

    def test_gist_index_used_for_knn(
        self, client, cashier_headers, manager_headers, make_product, open_drawer, db
    ):
        product = make_product(manager_headers, name="Idx", sku="SKU-IDX")
        open_drawer(cashier_headers)
        order = _tracked_order(client, cashier_headers, product["id"])
        _assign(client, manager_headers, order["id"])
        db.execute(text("SET enable_seqscan = off"))
        rows = db.execute(
            text(
                """
                EXPLAIN (COSTS OFF)
                SELECT id FROM orders
                ORDER BY destination <-> point(106.8, 6.2)
                LIMIT 5
                """
            )
        ).fetchall()
        assert any("ix_orders_destination_gist" in r[0] for r in rows), rows


class TestSseEvents:
    def test_tracking_event_published_on_location_report(
        self, client, cashier_headers, manager_headers, make_product, open_drawer
    ):
        from sqlalchemy.orm import Session

        from app.core.database import SessionLocal
        from app.models.tenant import Tenant
        from app.services.serving import serving_hub

        product = make_product(manager_headers, name="Sse", sku="SKU-SSE")
        open_drawer(cashier_headers)
        order = _tracked_order(client, cashier_headers, product["id"])
        _assign(client, manager_headers, order["id"])

        db: Session = SessionLocal()
        try:
            tenant = db.query(Tenant).filter(Tenant.slug == "default").one()
            import asyncio

            loop = asyncio.new_event_loop()

            async def _subscribe():
                return serving_hub.subscribe(tenant.id)

            wrapper = loop.run_until_complete(_subscribe())
            try:
                resp = client.post(
                    f"/api/v1/orders/tracking/{order['id']}/location",
                    headers=manager_headers,
                    json={"lat": 6.25, "lng": 106.85, "source": "gps"},
                )
                assert resp.status_code == 200, resp.text
                event = loop.run_until_complete(wrapper.get(2.0))
                assert event is not None
                assert event["tracking_status"] == "assigned"
                assert event["lat"] == 6.25
                assert event["lng"] == 106.85
            finally:
                serving_hub.unsubscribe(tenant.id, wrapper)
                loop.close()
        finally:
            db.close()


class TestPermissions:
    def test_cashier_denied_tracking_actions(
        self, client, cashier_headers, manager_headers, make_product, open_drawer, db
    ):
        product = make_product(manager_headers, name="Perm", sku="SKU-PERM")
        open_drawer(cashier_headers)
        order = _tracked_order(client, cashier_headers, product["id"])

        resp = client.post(
            f"/api/v1/orders/tracking/{order['id']}/status",
            headers=cashier_headers,
            json={"status": "assigned"},
        )
        assert resp.status_code == 403, resp.text
        resp = client.get("/api/v1/orders/tracking/", headers=cashier_headers)
        assert resp.status_code == 403, resp.text

    def test_service_agent_can_track(
        self,
        client,
        auth_factory,
        assign_role,
        cashier_headers,
        manager_headers,
        make_product,
        open_drawer,
    ):
        user = auth_factory.register("agent@example.com")
        assign_role(user["id"], "service_agent")
        agent_headers = auth_factory.login("agent@example.com")

        product = make_product(manager_headers, name="Agent", sku="SKU-AGENT")
        open_drawer(cashier_headers)
        order = _tracked_order(client, cashier_headers, product["id"])

        resp = client.post(
            f"/api/v1/orders/tracking/{order['id']}/status",
            headers=agent_headers,
            json={"status": "assigned"},
        )
        assert resp.status_code == 200, resp.text
        resp = client.post(
            f"/api/v1/orders/tracking/{order['id']}/location",
            headers=agent_headers,
            json={"lat": 6.2, "lng": 106.8},
        )
        assert resp.status_code == 200, resp.text
        resp = client.get("/api/v1/orders/tracking/", headers=agent_headers)
        assert resp.status_code == 200, resp.text

    def test_tenant_isolation_of_tracking(
        self,
        client,
        auth_factory,
        cashier_headers,
        manager_headers,
        make_product,
        open_drawer,
    ):
        _tenant_mode.FORCE_DEFAULT_TENANT = False
        try:
            product = make_product(manager_headers, name="Tiso", sku="SKU-TISO")
            open_drawer(cashier_headers)
            order = _tracked_order(client, cashier_headers, product["id"])
            _assign(client, manager_headers, order["id"])

            other = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "other@example.com",
                    "password": "TestPass123",
                    "full_name": "Other",
                },
            )
            other_id = other.json()["id"]
            db = None
            from app.core.database import SessionLocal

            db = SessionLocal()
            try:
                from app.models.rbac import Role
                from app.models.user import User

                other_user = db.get(User, other_id)
                role = db.query(Role).filter(Role.name == "service_agent").one()
                other_user.roles.append(role)
                db.commit()
            finally:
                db.close()
            other_headers = auth_factory.login("other@example.com")

            active = client.get("/api/v1/orders/tracking/", headers=other_headers)
            assert active.status_code == 200
            assert active.json() == []
        finally:
            _tenant_mode.FORCE_DEFAULT_TENANT = True


class TestOfflineSyncReplay:
    def test_location_update_event_replays_and_is_idempotent(
        self, client, cashier_headers, manager_headers, make_product, open_drawer
    ):
        product = make_product(manager_headers, name="SyncTr", sku="SKU-SYNTR")
        open_drawer(cashier_headers)
        order = _tracked_order(client, cashier_headers, product["id"])
        _assign(client, manager_headers, order["id"])

        event = {
            "client_event_id": "evt-loc-1",
            "event_type": "order_location_update",
            "idempotency_key": "sync-loc-1",
            "payload": {
                "order_id": order["id"],
                "lat": 6.23,
                "lng": 106.83,
                "source": "offline",
            },
        }
        for _ in range(2):
            resp = client.post(
                "/api/v1/sync/events/batch",
                headers=manager_headers,
                json={"events": [event]},
            )
            assert resp.status_code == 200, resp.text
            assert resp.json()["results"][0]["status"] in ("success", "duplicate")

        active = client.get("/api/v1/orders/tracking/", headers=manager_headers).json()
        assert active[0]["latest_location"]["lat"] == 6.23
        assert active[0]["latest_location"]["source"] == "offline"

        # Idempotent: same client_event_id does not double-append.
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            from app.models.order import OrderLocationUpdate

            count = (
                db.query(OrderLocationUpdate)
                .filter(OrderLocationUpdate.order_id == order["id"])
                .count()
            )
            assert count == 1
        finally:
            db.close()
