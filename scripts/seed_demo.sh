#!/usr/bin/env bash
# Seed a small, curated demo dataset for documentation screenshots.
#
# Creates (idempotently, via the public API):
#   - a demo user + tenant (owner role)
#   - categories, products (some below reorder point for the restock
#     workflow), customers, an open drawer, paid orders, a supplier,
#     an ordered purchase order, and an approved invoice
#
# Usage: BASE_URL=http://localhost:8001 ./scripts/seed_demo.sh

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
EMAIL="${DEMO_EMAIL:-demo@example.com}"
PASSWORD="${DEMO_PASSWORD:-DemoPass123}"

jq_ok() { echo "$1" | jq -e "$2" >/dev/null 2>&1; }

echo "== login or register ${EMAIL} =="
TOKEN=$(curl -sS -X POST "${BASE_URL}/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "username=${EMAIL}" \
  --data-urlencode "password=${PASSWORD}" \
  --data-urlencode "grant_type=password" | jq -r '.access_token // empty')

if [[ -z "$TOKEN" ]]; then
  REG=$(curl -sS -X POST "${BASE_URL}/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"${EMAIL}\", \"password\": \"${PASSWORD}\", \"full_name\": \"Demo User\"}")
  jq_ok "$REG" '.id' || { echo "register failed: $REG" >&2; exit 1; }
  TOKEN=$(curl -sS -X POST "${BASE_URL}/api/v1/auth/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "username=${EMAIL}" \
    --data-urlencode "password=${PASSWORD}" \
    --data-urlencode "grant_type=password" | jq -r '.access_token')
fi
AUTH="Authorization: Bearer ${TOKEN}"

api() { curl -sS -H "$AUTH" -H "Content-Type: application/json" "$@"; }

COUNT=$(api "${BASE_URL}/api/v1/products/?limit=1" | jq 'length')
if [[ "$COUNT" -gt 0 ]]; then
  echo "products already present (${COUNT}); skipping seed"
  exit 0
fi

echo "== categories =="
COFFEE=$(api -X POST "${BASE_URL}/api/v1/products/categories" -d '{"name": "Coffee", "color": "#F3E5F5"}' | jq -r '.id')
PASTRY=$(api -X POST "${BASE_URL}/api/v1/products/categories" -d '{"name": "Pastry", "color": "#FFF3E0"}' | jq -r '.id')
DRINKS=$(api -X POST "${BASE_URL}/api/v1/products/categories" -d '{"name": "Beverages", "color": "#E3F2FD"}' | jq -r '.id')
echo "coffee=${COFFEE} pastry=${PASTRY} drinks=${DRINKS}"

echo "== products =="
mk_product() {
  local name sku price stock reorder color
  name="$1"; sku="$2"; price="$3"; stock="$4"; reorder="$5"; color="$6"
  api -X POST "${BASE_URL}/api/v1/products/" -d "{
    \"name\": \"${name}\",
    \"sku\": \"${sku}\",
    \"description\": \"${name} — demo catalog item for the POS.\",
    \"price\": ${price},
    \"unit_cost\": 2.00,
    \"stock_quantity\": ${stock},
    \"min_stock\": 10,
    \"reorder_point\": ${reorder},
    \"category_id\": ${color}
  }" | jq -r '.id'
}

# Low-stock items (stock < reorder_point) feed the restock workflow.
P1=$(mk_product "House Blend Coffee" "DEMO-CFB-01" 6.50 5 15 "$COFFEE")
P2=$(mk_product "Single-Origin Sumatra" "DEMO-CFB-02" 8.00 8 20 "$COFFEE")
P3=$(mk_product "Butter Croissant" "DEMO-PST-01" 3.75 40 8 "$PASTRY")
P4=$(mk_product "Chocolate Danish" "DEMO-PST-02" 4.25 35 10 "$PASTRY")
P5=$(mk_product "Espresso" "DEMO-DRK-01" 3.00 120 25 "$DRINKS")
P6=$(mk_product "Matcha Latte" "DEMO-DRK-02" 5.50 60 15 "$DRINKS")
P7=$(mk_product "Cold Brew" "DEMO-DRK-03" 4.75 90 20 "$DRINKS")
echo "products: $P1 $P2 $P3 $P4 $P5 $P6 $P7"

echo "== customers =="
C1=$(api -X POST "${BASE_URL}/api/v1/customers/" -d '{"name": "Alice Wang", "email": "alice@example.com", "phone": "+12025550101"}' | jq -r '.id')
C2=$(api -X POST "${BASE_URL}/api/v1/customers/" -d '{"name": "Bob Martinez", "email": "bob@example.com", "phone": "+12025550102"}' | jq -r '.id')
C3=$(api -X POST "${BASE_URL}/api/v1/customers/" -d '{"name": "Sara Kim", "email": "sara@example.com", "phone": "+12025550103"}' | jq -r '.id')
echo "customers: $C1 $C2 $C3"

echo "== drawer =="
DRAWER=$(api -X POST "${BASE_URL}/api/v1/drawers/open" -d '{"starting_cash": 500.0}' | jq -r '.id // empty')
echo "drawer=${DRAWER}"

echo "== orders + payments =="
mk_order() {
  local pid1 pid2 cust total
  pid1="$1"; pid2="$2"; cust="$3"; total="$4"
  OID=$(api -X POST "${BASE_URL}/api/v1/orders/" -d "{
    \"customer_id\": ${cust},
    \"items\": [{\"product_id\": ${pid1}, \"quantity\": 2}, {\"product_id\": ${pid2}, \"quantity\": 1}]
  }" | jq -r '.id')
  api -X POST "${BASE_URL}/api/v1/orders/${OID}/payments" \
    -d "{\"payment_method\": \"card\", \"amount\": ${total}}" >/dev/null
  echo "$OID"
}
O1=$(mk_order "$P5" "$P3" "$C1" 11.75)
O2=$(mk_order "$P6" "$P1" "$C2" 17.50)
O3=$(mk_order "$P7" "$P4" "$C3" 13.75)
O4=$(mk_order "$P5" "$P7" "$C1" 10.75)
O5=$(mk_order "$P3" "$P2" "$C2" 15.50)
echo "orders: $O1 $O2 $O3 $O4 $O5"

echo "== supplier + purchase order + invoice =="
SUP=$(api -X POST "${BASE_URL}/api/v1/purchasing/suppliers" \
  -d '{"name": "Sumatra Roastery", "contact_email": "sales@sumatra.example", "phone": "+12025550999"}' | jq -r '.id')
echo "supplier=${SUP}"

PO=$(api -X POST "${BASE_URL}/api/v1/purchasing/orders" -d "{
  \"supplier_id\": ${SUP},
  \"notes\": \"Weekly restock\",
  \"items\": [
    {\"product_id\": ${P1}, \"quantity_ordered\": 50, \"unit_cost\": 2.50},
    {\"product_id\": ${P2}, \"quantity_ordered\": 40, \"unit_cost\": 3.00}
  ]
}" | jq -r '.id')
api -X POST "${BASE_URL}/api/v1/purchasing/orders/${PO}/submit-review" -d '{}' >/dev/null
api -X POST "${BASE_URL}/api/v1/purchasing/orders/${PO}/mark-ordered" -d '{}' >/dev/null
echo "purchase order=${PO} (ordered)"

PO_ITEMS=$(api "${BASE_URL}/api/v1/purchasing/orders/${PO}/detail" | jq -r '.items[].id' 2>/dev/null || true)
INV=$(api -X POST "${BASE_URL}/api/v1/purchasing/invoices" -d "{
  \"purchase_order_id\": ${PO},
  \"invoice_number\": \"INV-2026-0001\",
  \"items\": [$(echo "$PO_ITEMS" | head -1 | xargs -I{} printf '{"purchase_order_item_id": %s, "billed_quantity": 50, "billed_unit_cost": 2.50}' {})]
}" | jq -r '.id')
api -X POST "${BASE_URL}/api/v1/purchasing/invoices/${INV}/submit-review" -d '{}' >/dev/null
api -X POST "${BASE_URL}/api/v1/purchasing/invoices/${INV}/approve" -d '{}' >/dev/null
echo "invoice=${INV} (approved)"

echo "== seed complete: ${BASE_URL} =="
