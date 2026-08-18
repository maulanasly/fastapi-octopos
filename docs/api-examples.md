[Back to README](../README.md)

# API Examples

## Authentication

**Register a new user:**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "full_name": "User Name",
    "password": "secure-password"
  }'
```

**Login (get JWT tokens):**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=secure-password"
```

## Create Order

```bash
curl -X POST http://127.0.0.1:8000/api/v1/orders/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"product_id": 1, "quantity": 2},
      {"product_id": 2, "quantity": 1}
    ],
    "customer_id": 1
  }'
```

## Add Payment

```bash
curl -X POST http://127.0.0.1:8000/api/v1/orders/1/payments \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 50000,
    "payment_method": "cash"
  }'
```

## Sync Events (Offline Clients)

```bash
curl -X POST http://127.0.0.1:8000/api/v1/sync/events/batch \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "client_event_id": "evt-001",
        "event_type": "order_create",
        "payload": {
          "items": [{"product_id": 1, "quantity": 1}],
          "idempotency_key": "order-001"
        }
      }
    ]
  }'
```

## Pull Sync (Terminals)

Offline terminals pull catalog changes and check their event queue:

```bash
# Delta catalog since a watermark (omit ?since= for a full first sync)
curl -G http://127.0.0.1:8000/api/v1/sync/catalog \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  --data-urlencode "since=2026-08-16T00:00:00Z"

# Status of processed offline events
curl http://127.0.0.1:8000/api/v1/sync/events?status=success \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Health & Operations

```bash
curl http://127.0.0.1:8000/api/v1/health        # liveness
curl http://127.0.0.1:8000/api/v1/health/ready  # readiness (DB check)
```

Every response carries an `X-Request-ID` header echoed into log lines
(`request_id=...`) for request correlation.

## Audit Trail

Sensitive operations (refunds, stock adjustments, drawer reconciliation,
RBAC changes) are recorded in `audit_logs`. Superusers query them via:

```bash
curl http://127.0.0.1:8000/api/v1/audit/logs?action=refund.create \
  -H "Authorization: Bearer SUPERUSER_TOKEN"
```

## Shift Reports (Z-Reports)

```bash
# JSON Z-report for one closed shift
curl http://127.0.0.1:8000/api/v1/reports/shift/{reconciliation_id} \
  -H "Authorization: Bearer TOKEN"

# End-of-day summary across shifts
curl "http://127.0.0.1:8000/api/v1/reports/daily-close?report_date=2026-08-16" \
  -H "Authorization: Bearer TOKEN"
```

Print-friendly versions are available in the admin dashboard
(`/admin/reports` -> "Shift Reports").
