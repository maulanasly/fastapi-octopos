# Purchasing Flow & Redesign Plan

The intended purchasing lifecycle and the phased redesign. Phase 1 (the
"make it usable" baseline), the replenishment UX (Phase 2), the supplier
payment recording (Phase 3 financials), the requester-vs-approver
separation (Phase 4), and purchasing visibility (Phase 5) are implemented;
the remaining spec items are listed at the end.

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
4. **PO review & approval** — `submit_purchase_order_for_review`
   (`POST /purchasing/orders/{id}/submit-review`) moves a draft to
   `pending_review`; `mark_purchase_order_ordered` now acts as the approve
   step (only `pending_review` POs, sets `ordered` + `ordered_at`), and
   `POST /purchasing/orders/{id}/reject` → `rejected`. Approval requires
   `purchasing:approve` **and** a different user than the creator (strict
   4-eyes; superusers exempt — keeps the admin panel workflow working).
   Admin: the Restock workflow's "order" step submits then approves in one
   action.
5. **Receive goods** — `receive_purchase_order_items`: partial or full;
   only `ordered` / `partially_received` POs can receive (draft/rejected/
   cancelled cannot); updates `quantity_received`, product stock + unit
   cost, and records a `StockMovement`; PO auto-transitions to
   `partially_received`/`received` with `received_at`.
6. **Invoice / payable** — `create_purchase_invoice` against received
   quantities (`invoice_number`, per-item billed qty/cost) computes
   **quantity and price variance** vs the PO; status `draft`. Then
   `submit_purchase_invoice_for_review` → `pending_review`, and
   `approve_purchase_invoice` → `approved` (`approved_at`, the financial
   recognition point) or `reject` → `rejected`. Approval requires
   `purchasing:approve` and a different user than the creator (4-eyes).
7. **Supplier payment** — `create_supplier_payment`
   (`POST /purchasing/payments`) records a payment against an **approved**
   invoice (amount, method, reference, optional payment date); partial
   payments are allowed and overpayment is rejected
   (outstanding = invoice total − approved payments). Same review workflow:
   `draft → pending_review → approved | rejected` via
   `submit-review` / `approve` / `reject`, with the same 4-eyes rule.
   Approval is the paid recognition point.

Status enums:

- `purchase_orders.status`: `draft → pending_review → ordered →
  partially_received → received`, or `rejected | cancelled`.
- `purchase_invoices.status`: `draft → pending_review → approved | rejected`.
- `supplier_payments.status`: `draft → pending_review → approved | rejected`.

## RBAC

- `purchasing:manage` — create suppliers/POs/invoices/payments and submit
  them for review (router-wide on `/purchasing/*`).
- `purchasing:approve` — approve/reject invoices, orders, and payments
  (endpoint-level). The seeded **manager** role has `purchasing:manage`
  only; the **admin** role has both. Approvers see the tenant's full review
  queue (lists are not filtered to own rows for approvers).
- 4-eyes: a non-superuser cannot approve/reject an invoice, order, or
  payment they created (403 "you created"). Superusers (admin panel) are
  exempt.

## Audit trail

Purchasing lifecycle actions are recorded via `log_action`
(`app/core/audit.py`) into `audit_logs`: `purchase_order.create/submit/
approve/reject/cancel/receive`, `purchase_invoice.create/submit/approve/
reject`, `supplier_payment.create/submit/approve/reject`. Viewable via
`GET /api/v1/audit/logs`.

## Reporting

- `GET /reports/purchase-invoices` — invoice counts/approved totals/
  variance (`get_invoice_summary_data`).
- `GET /reports/supplier-payments` — payment counts/approved total and
  `outstanding_payable` (approved invoice total − approved payments).
- Admin dashboard: Supplier Paid Total and Supplier Outstanding cards.

## Client (Flutter)

- Purchase orders: draft POs get **Submit for review**; pending review
  POs show **Approve**/**Reject** for users with `purchasing:approve`
  (status chips include `pending_review`/`rejected`).
- Invoices: create dialog now edits per-line billed qty/cost (defaults to
  received qty + PO cost) and sets `invoice_date`/`due_date`.
- Payments tab: list with status filter, create-payment dialog (approved
  invoice, amount, method, reference), detail + submit/approve/reject.

## Replenishment UX (Phase 2)

- `GET /inventory/replenishment-suggestions` now returns `unit_cost`
  (product price) and the suggested supplier per product
  (`suggested_supplier_id`/`suggested_supplier_name`, resolved from
  PO/invoice history with the sole-active-supplier fallback).
- `POST /purchasing/orders/batch-from-replenishment` creates one draft PO
  per supplier in a single call. It accepts per-product overrides
  (`quantity_ordered`, `unit_cost`, `supplier_id`), skips products already
  covered by a pending PO, without supplier history, or with an
  inactive/unknown supplier — every skip comes back with its reason in
  `skipped_products`.
- Client (Inventory → Replenishment): suggestion rows are editable —
  quantity, unit cost, and a per-row supplier dropdown defaulting to the
  suggested supplier. **Generate POs** batches the included rows through
  the new endpoint and surfaces created POs plus skip reasons.

## Purchasing Visibility (Phase 3)

- `GET /purchasing/orders/{id}/detail` returns a consolidated PO detail:
  per-item `quantity_invoiced`/`billed_total` (from non-rejected invoice
  items), a lifecycle `timeline` (created → ordered → receipts from stock
  movements → invoice created/approved/rejected events), and totals
  (`total_received_amount`, `total_billed_amount`, `outstanding_payable`).
  Approvers see all tenant POs; requesters their own.
- `GET /purchasing/suppliers/{id}/ledger` returns the supplier ledger:
  open PO count/amount, pending-review invoice count/amount, approved
  invoice and payment totals, outstanding payable, plus up to 50 merged
  recent entries (POs, invoices, payments) newest-first.
- Reports: `GET /reports/supplier-spend` (per-supplier PO/invoice counts,
  approved spend, variance, sorted by spend, with a COGS estimate =
  approved invoice total) and `GET /reports/purchase-variance` (monthly
  billed/approved/variance buckets, dialect-safe Python grouping).
- Client: the PO dialog now shows invoiced columns, the timeline, and
  totals; Purchasing gains a **Ledger** tab (supplier list → ledger
  dialog); Reports gains **Supplier spend** and **Purchase variance
  trend** cards.

## Purchasing automation (Phase 6)

The scheduled auto-PO task (`app/services/auto_po.py`, driven by the
`REPLENISHMENT_AUTO_PO_ENABLED` loop in `app/main.py`) is now configurable
per tenant:

- `PurchasingSetting` model (singleton per tenant, migration `0019`) with
  `auto_po_enabled` (default off), `auto_po_lookback_days` (default 30) and
  `auto_po_min_stock_trigger` (default 0). The env flag remains the master
  gate for the background loop; the per-tenant flag decides whether that
  tenant gets drafts.
- The effective reorder line is `max(reorder_point, min_stock_trigger)`;
  the trigger also raises the suggested target stock so generated POs have
  a positive order quantity.
- `GET/PUT /purchasing/settings` expose the settings to signed-in users;
  the admin panel gains a "Purchasing Automation" view with singleton
  enforcement.
- The purchasing screen's app-bar gear opens an automation settings dialog
  (enable switch, lookback days, min stock trigger).

## Remaining spec (not implemented)

- None — all planned phases are implemented.
