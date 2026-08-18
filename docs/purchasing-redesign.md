# Purchasing Flow & Redesign Plan

The intended purchasing lifecycle and a phased redesign proposal. Phase 1
(the "make it usable" baseline) is implemented; phases 2–4 are a spec for
later work.

## Intended lifecycle

1. **Suppliers** — CRUD via `POST/GET /purchasing/suppliers` and the admin
   `SupplierAdmin` view. A supplier belongs to a tenant and has an active
   flag.
2. **Replenishment** — `build_replenishment_suggestions`
   (`app/core/replenishment.py`) looks at products at/below `reorder_point`
   and, using a sales lookback window, produces `should_reorder` +
   `recommended_order_quantity` per product.
3. **Create PO** (status `draft`) — two paths:
   - *Auto*: `auto_generate_purchase_orders` (`app/services/auto_po.py`)
     groups suggestions by each product's most-recent supplier (from PO /
     invoice history), with a fallback to the tenant's sole active supplier;
     creates one draft PO per supplier, attributed to the first active
     superuser.
   - *Manual*: `create_purchase_order` (`POST /purchasing/orders`) — the
     admin Restock workflow now exposes this via the **Create PO** step
     (supplier + product qty/cost rows), so POs can be raised even when
     inventory is healthy.
4. **Mark ordered** — `mark_purchase_order_ordered` sets `ordered` +
   `ordered_at` (PO confirmed/sent). Admin: button on a draft PO in the
   Receive step.
5. **Receive goods** — `receive_purchase_order_items`: partial or full;
   updates `quantity_received`, product stock + unit cost, and records a
   `StockMovement`; PO auto-transitions to `partially_received`/`received`
   with `received_at`.
6. **Invoice / payable** — `create_purchase_invoice` against received
   quantities (`invoice_number`, per-item billed qty/cost) computes
   **quantity and price variance** vs the PO; status `draft`. Then
   `submit_purchase_invoice_for_review` → `pending_review`, and
   `approve_purchase_invoice` → `approved` (`approved_at`, the financial
   recognition point) or `reject` → `rejected`.

Status enums:

- `purchase_orders.status`: `draft → ordered → partially_received →
  received`, or `cancelled`.
- `purchase_invoices.status`: `draft → pending_review → approved | rejected`.

## Phase 1 — implemented

- Manual **Create PO** step in the Restock workflow (`app/templates/
  workflows/restock.html`, `app/admin/views.py`).
- **Mark ordered** action for draft POs in the Receive step.
- Workflow queries (restock low-stock/pending/draft, invoice eligible POs,
  dashboard counts) scoped to `ADMIN_TENANT_ID`.
- `_supplier_for_products` fallback to the tenant's sole active supplier.

## Phase 2 — replenishment UX (spec)

- Suggestion table with editable `recommended_order_quantity` and unit cost
  before generating; allow per-row supplier overrides.
- Surface skip reasons (no supplier / inactive supplier / already in a
  pending PO) inline instead of as a flash message.
- Batch "generate for all suppliers" vs per-supplier review.

## Phase 3 — lifecycle visibility & financials (spec)

- Consolidated PO detail: timeline draft → ordered → received → invoiced,
  with per-item received/invoiced totals and variance summary.
- Supplier ledger: open POs, pending invoices, total payable (sum of
  approved invoices not yet paid). Note: there is currently **no supplier
  payment recording** — a `payments` model for suppliers (payment date,
  amount, method, reference) is a larger addition; "payable" today means
  approved invoices.
- Invoice review page surfacing `has_quantity_variance` /
  `has_price_variance` with approve/reject rationale.
- Purchasing reports: COGS via received unit cost, spend by supplier,
  variance trends over time.

## Phase 4 — automation & config (spec)

- Settings for the scheduled auto-PO task (`REPLENISHMENT_*`): enable flag,
  lookback days, min stock trigger.
- Optional requester-vs-approver separation using the existing
  `purchasing:manage` / `purchasing:approve` RBAC permissions (approve
  requires a user without `purchasing:manage`).
