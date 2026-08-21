#!/usr/bin/env bash
# Idempotent API seeding for load tests.
#
# Creates (if missing):
#   - a load-test user (tenant owner, first registration wins the owner role)
#   - PRODUCTS products with searchable descriptions
#   - CUSTOMERS customers
#   - ORDERS orders (only if the current count is below target)
#
# Usage: BASE_URL=http://localhost:8000 ./loadtest/seed.sh

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
EMAIL="${EMAIL:-loadtest@example.com}"
PASSWORD="${PASSWORD:-Loadtest123}"
PRODUCTS="${PRODUCTS:-100}"
CUSTOMERS="${CUSTOMERS:-30}"
ORDERS="${ORDERS:-50}"

login() {
  curl -sS -X POST "${BASE_URL}/api/v1/auth/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "username=${EMAIL}" \
    --data-urlencode "password=${PASSWORD}" \
    --data-urlencode "grant_type=password"
}

echo "== seed: login or register ${EMAIL} =="
TOKEN=$(login | jq -r '.access_token // empty')
if [[ -z "$TOKEN" ]]; then
  echo "no token, registering..."
  REG=$(curl -sS -X POST "${BASE_URL}/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"${EMAIL}\", \"password\": \"${PASSWORD}\", \"full_name\": \"Load Test\"}")
  echo "$REG" | jq -e '.id' >/dev/null || { echo "register failed: $REG" >&2; exit 1; }
  TOKEN=$(login | jq -r '.access_token // empty')
  [[ -n "$TOKEN" ]] || { echo "login after register failed" >&2; exit 1; }
fi
AUTH="Authorization: Bearer ${TOKEN}"

total_count() { # $1 = resource path
  curl -sS -D - -o /dev/null -H "$AUTH" "${BASE_URL}${1}" \
    | awk 'tolower($1)=="x-total-count:" {gsub(/\r/, "", $2); print $2}'
}

TOTAL_PRODUCTS=$(total_count "/api/v1/products/?limit=1")
echo "products in DB: ${TOTAL_PRODUCTS:-0}"
if (( TOTAL_PRODUCTS < PRODUCTS )); then
  echo "creating $((PRODUCTS - TOTAL_PRODUCTS)) products..."
  for ((i = TOTAL_PRODUCTS + 1; i <= PRODUCTS; i++)); do
    SKU="LT-$(printf '%05d' "$i")"
    BODY=$(cat <<JSON
{
  "name": "Loadtest Coffee Blend ${i}",
  "sku": "${SKU}",
  "description": "Loadtest product ${i}: single origin coffee blend number ${i}, notes of chocolate and citrus.",
  "price": $((5 + i % 20)).99,
  "unit_cost": 2.50,
  "stock_quantity": 1000,
  "min_stock": 10,
  "reorder_point": 20
}
JSON
)
    RES=$(curl -sS -X POST -H "$AUTH" -H "Content-Type: application/json" \
      -d "$BODY" "${BASE_URL}/api/v1/products/")
    echo "$RES" | jq -e '.id' >/dev/null || echo "product ${SKU} skipped: $(echo "$RES" | head -c 120)"
  done
else
  echo "products target met"
fi

CUSTOMER_COUNT=$(curl -sS -H "$AUTH" "${BASE_URL}/api/v1/customers/?limit=1000" | jq 'length' 2>/dev/null || echo 0)
if (( CUSTOMER_COUNT < CUSTOMERS )); then
  echo "creating $((CUSTOMERS - CUSTOMER_COUNT)) customers..."
  for ((i = CUSTOMER_COUNT + 1; i <= CUSTOMERS; i++)); do
    BODY="{\"name\": \"Loadtest Customer ${i}\", \"email\": \"lt-customer-${i}@example.com\", \"phone\": \"+1555000${i}\"}"
    RES=$(curl -sS -X POST -H "$AUTH" -H "Content-Type: application/json" \
      -d "$BODY" "${BASE_URL}/api/v1/customers/")
    echo "$RES" | jq -e '.id' >/dev/null || echo "customer ${i} skipped: $(echo "$RES" | head -c 120)"
  done
else
  echo "customers target met"
fi

ORDER_COUNT=$(curl -sS -H "$AUTH" "${BASE_URL}/api/v1/orders/?limit=1000" | jq 'length' 2>/dev/null || echo 0)
if (( ORDER_COUNT < ORDERS )); then
  echo "creating $((ORDERS - ORDER_COUNT)) orders..."
  # Orders require an open drawer session for the user.
  DRAWER=$(curl -sS -H "$AUTH" "${BASE_URL}/api/v1/drawers/active" | jq -r '.id // empty')
  if [[ -z "$DRAWER" ]]; then
    RES=$(curl -sS -X POST -H "$AUTH" -H "Content-Type: application/json" \
      -d '{"starting_cash": 500.0}' "${BASE_URL}/api/v1/drawers/open")
    DRAWER=$(echo "$RES" | jq -r '.id // empty')
    [[ -n "$DRAWER" ]] || echo "drawer open failed: $(echo "$RES" | head -c 120)"
  fi
  PRODUCT_IDS=$(curl -sS -H "$AUTH" "${BASE_URL}/api/v1/products/?limit=100" | jq -c '[.[].id]')
  N_IDS=$(echo "$PRODUCT_IDS" | jq 'length')
  if (( N_IDS == 0 )); then
    echo "no products to order, skipping orders" >&2
    exit 0
  fi
  for ((i = ORDER_COUNT + 1; i <= ORDERS; i++)); do
    PID=$(echo "$PRODUCT_IDS" | jq ".[$((i % N_IDS))]")
    BODY="{\"items\": [{\"product_id\": ${PID}, \"quantity\": $((1 + i % 3))}]}"
    RES=$(curl -sS -X POST -H "$AUTH" -H "Content-Type: application/json" \
      -d "$BODY" "${BASE_URL}/api/v1/orders/")
    echo "$RES" | jq -e '.id' >/dev/null || echo "order ${i} skipped: $(echo "$RES" | head -c 120)"
  done
else
  echo "orders target met"
fi

echo "== seed complete =="
