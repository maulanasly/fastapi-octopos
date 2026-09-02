from datetime import UTC, datetime
from uuid import uuid4

# pyrefly: ignore [missing-import]
from sqladmin import BaseView, Flash, expose
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from starlette.exceptions import HTTPException

# pyrefly: ignore [missing-import]
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.admin.base import _selected_tenant_id
from app.core.audit import log_action
from app.core.database import SessionLocal
from app.core.replenishment import build_replenishment_suggestions
from app.models.drawer import DrawerSession
from app.models.order import Order
from app.models.product import Product
from app.models.purchase import (
    PurchaseInvoice,
    PurchaseInvoiceItem,
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
    SupplierPayment,
)
from app.models.refund import RefundItem
from app.models.shift_reconciliation import ShiftReconciliation
from app.models.user import User
from app.schemas.drawer import ShiftReconciliationCreate
from app.schemas.purchase import (
    PurchaseInvoiceCreate,
    PurchaseInvoiceItemCreate,
    PurchaseInvoiceReviewAction,
    PurchaseOrderCreate,
    PurchaseOrderItemCreate,
    PurchaseOrderReceive,
    PurchaseOrderReceiveItem,
    PurchaseOrderReviewAction,
    SupplierPaymentReviewAction,
)
from app.schemas.refund import RefundCreate, RefundItemCreate
from app.services.auto_po import auto_generate_purchase_orders
from app.services.drawers import build_reconciliation, compute_drawer_totals
from app.services.purchasing import (
    approve_purchase_invoice,
    approve_supplier_payment,
    create_purchase_invoice,
    create_purchase_order,
    mark_purchase_order_ordered,
    receive_purchase_order_items,
    reject_purchase_invoice,
    reject_supplier_payment,
    submit_purchase_invoice_for_review,
    submit_purchase_order_for_review,
)
from app.services.refunds import create_refund


class WorkflowsAdmin(BaseView):
    """Guided admin workflows: restock, invoicing, drawer close, refunds.

    Each wizard is a stateless step chain under one route, driving the same
    service layer the public API uses (``app.services.*``).
    """

    name = "Workflows"
    icon = "fa-solid fa-wand-magic-sparkles"
    category = "Workflows"
    category_icon = "fa-solid fa-bolt"

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _admin_user(db, request):
        return db.get(User, request.session.get("admin_user_id"))

    @staticmethod
    def _flash_http_error(request, exc: HTTPException):
        Flash.error(request, str(exc.detail), "Action failed")

    @staticmethod
    def _previously_billed_map(db, po_item_ids) -> dict[int, int]:
        if not po_item_ids:
            return {}
        rows = (
            db.query(
                PurchaseInvoiceItem.purchase_order_item_id,
                func.coalesce(func.sum(PurchaseInvoiceItem.billed_quantity), 0),
            )
            .join(
                PurchaseInvoice,
                PurchaseInvoiceItem.invoice_id == PurchaseInvoice.id,
            )
            .filter(
                PurchaseInvoiceItem.purchase_order_item_id.in_(po_item_ids),
                PurchaseInvoice.status != "rejected",
            )
            .group_by(PurchaseInvoiceItem.purchase_order_item_id)
            .all()
        )
        return {row[0]: int(row[1] or 0) for row in rows}

    @staticmethod
    def _already_refunded_map(db, order_item_ids) -> dict[int, int]:
        if not order_item_ids:
            return {}
        rows = (
            db.query(
                RefundItem.order_item_id,
                func.coalesce(func.sum(RefundItem.quantity), 0),
            )
            .filter(RefundItem.order_item_id.in_(order_item_ids))
            .group_by(RefundItem.order_item_id)
            .all()
        )
        return {row[0]: int(row[1] or 0) for row in rows}

    # --------------------------------------------------------------- hub page

    @expose("/workflows", methods=["GET"])
    async def workflows_index(self, request: Request):
        db = SessionLocal()
        try:
            tenant_id = _selected_tenant_id(request)
            # Unified low-stock via replenishment.should_reorder
            all_products = (
                db.query(Product).filter(Product.tenant_id == tenant_id).all()
            )
            low_stock_count = sum(
                1
                for s in build_replenishment_suggestions(
                    db, all_products, lookback_days=30
                )
                if s.should_reorder
            )
            draft_po_count = (
                db.query(PurchaseOrder)
                .filter(
                    PurchaseOrder.status == "draft",
                    PurchaseOrder.tenant_id == _selected_tenant_id(request),
                )
                .count()
            )
            pending_invoice_count = (
                db.query(PurchaseInvoice)
                .filter(
                    PurchaseInvoice.status == "pending_review",
                    PurchaseInvoice.tenant_id == _selected_tenant_id(request),
                )
                .count()
            )
            pending_payment_count = (
                db.query(SupplierPayment)
                .filter(
                    SupplierPayment.status == "pending_review",
                    SupplierPayment.tenant_id == _selected_tenant_id(request),
                )
                .count()
            )
            open_drawer_count = (
                db.query(DrawerSession)
                .filter(
                    DrawerSession.status == "open",
                    DrawerSession.tenant_id == _selected_tenant_id(request),
                )
                .count()
            )
            return await self.templates.TemplateResponse(
                request,
                "workflows/index.html",
                context={
                    "title": "Workflows",
                    "low_stock_count": low_stock_count,
                    "draft_po_count": draft_po_count,
                    "pending_invoice_count": pending_invoice_count,
                    "pending_payment_count": pending_payment_count,
                    "open_drawer_count": open_drawer_count,
                },
            )
        finally:
            db.close()

    # ----------------------------------------------------------- restock flow

    @expose("/workflows/restock", methods=["GET", "POST"])
    async def restock_workflow(self, request: Request):
        db = SessionLocal()
        try:
            step = request.query_params.get("step", "generate")
            pending_product_ids = {
                row[0]
                for row in db.query(PurchaseOrderItem.product_id)
                .join(
                    PurchaseOrder,
                    PurchaseOrderItem.purchase_order_id == PurchaseOrder.id,
                )
                .filter(
                    PurchaseOrder.status.in_(
                        ("draft", "ordered", "partially_received")
                    ),
                    PurchaseOrder.tenant_id == _selected_tenant_id(request),
                )
                .all()
            }
            tenant_id = _selected_tenant_id(request)
            all_products = (
                db.query(Product).filter(Product.tenant_id == tenant_id).all()
            )
            candidates = [p for p in all_products if p.id not in pending_product_ids]
            suggestions = build_replenishment_suggestions(
                db, candidates, lookback_days=30
            )
            reorder_ids = {s.product_id for s in suggestions if s.should_reorder}
            low_stock = sorted(
                [p for p in candidates if p.id in reorder_ids], key=lambda p: p.id
            )

            if request.method == "POST":
                form = await request.form()
                step = form.get("step") or step
                if step == "generate":
                    try:
                        lookback_days = int(form.get("lookback_days") or 30)
                    except (TypeError, ValueError):
                        lookback_days = 30
                    result = auto_generate_purchase_orders(
                        db=db, lookback_days=lookback_days
                    )
                    if result["generated"]:
                        Flash.success(
                            request,
                            f"Generated {result['generated']} purchase order(s) "
                            f"for {', '.join(result['suppliers'])}.",
                        )
                    elif result["skipped_products"]:
                        reasons = {
                            item["reason"] for item in result["skipped_products"]
                        }
                        Flash.warning(
                            request,
                            "No POs generated. " + "; ".join(sorted(reasons)),
                        )
                    else:
                        Flash.info(request, "Nothing to reorder right now.")
                    return RedirectResponse(
                        url="/admin/workflows/restock?step=receive", status_code=303
                    )

                if step == "select_po":
                    try:
                        po_id = int(form.get("po_id") or "")
                    except (TypeError, ValueError):
                        raise HTTPException(
                            status_code=400, detail="Select a PO"
                        ) from None
                    return RedirectResponse(
                        url=f"/admin/workflows/restock?step=receive&po_id={po_id}",
                        status_code=303,
                    )

                if step == "create":
                    try:
                        supplier_id = int(form.get("supplier_id") or "")
                    except (TypeError, ValueError):
                        supplier_id = 0
                    try:
                        if supplier_id <= 0:
                            raise HTTPException(
                                status_code=400, detail="Select a supplier"
                            )
                        items = []
                        for key, value in form.multi_items():
                            if not key.startswith("qty_"):
                                continue
                            try:
                                product_id = int(key.removeprefix("qty_"))
                                qty = int(value)
                            except (TypeError, ValueError):
                                continue
                            if qty <= 0:
                                continue
                            try:
                                unit_cost = float(form.get(f"cost_{product_id}") or 0)
                            except (TypeError, ValueError):
                                unit_cost = 0.0
                            items.append(
                                PurchaseOrderItemCreate(
                                    product_id=product_id,
                                    quantity_ordered=qty,
                                    unit_cost=unit_cost,
                                )
                            )
                        if not items:
                            raise HTTPException(
                                status_code=400,
                                detail="Enter at least one product with a quantity",
                            )
                        user = self._admin_user(db, request)
                        if user is None:
                            raise HTTPException(
                                status_code=403, detail="Admin user missing"
                            )
                        purchase_order = create_purchase_order(
                            db=db,
                            current_user=user,
                            purchase_order_in=PurchaseOrderCreate(
                                supplier_id=supplier_id,
                                items=items,
                                notes=form.get("notes") or None,
                            ),
                            tenant_id=_selected_tenant_id(request),
                        )
                    except HTTPException as exc:
                        self._flash_http_error(request, exc)
                        return RedirectResponse(
                            url="/admin/workflows/restock?step=create",
                            status_code=303,
                        )
                    Flash.success(
                        request, f"Purchase order #{purchase_order.id} created (draft)."
                    )
                    return RedirectResponse(
                        url=f"/admin/workflows/restock?step=receive&po_id={purchase_order.id}",
                        status_code=303,
                    )

                if step == "order":
                    try:
                        po_id = int(form.get("po_id") or "")
                    except (TypeError, ValueError):
                        raise HTTPException(
                            status_code=400, detail="Select a PO"
                        ) from None
                    try:
                        user = self._admin_user(db, request)
                        if user is None:
                            raise HTTPException(
                                status_code=403, detail="Admin user missing"
                            )
                        tenant_id = _selected_tenant_id(request)
                        submit_purchase_order_for_review(
                            db=db,
                            current_user=user,
                            purchase_order_id=po_id,
                            action_in=PurchaseOrderReviewAction(review_note=None),
                            tenant_id=tenant_id,
                        )
                        mark_purchase_order_ordered(
                            db=db,
                            current_user=user,
                            purchase_order_id=po_id,
                            action_in=PurchaseOrderReviewAction(review_note=None),
                            tenant_id=tenant_id,
                        )
                    except HTTPException as exc:
                        self._flash_http_error(request, exc)
                        return RedirectResponse(
                            url=f"/admin/workflows/restock?step=receive&po_id={po_id}",
                            status_code=303,
                        )
                    Flash.success(
                        request, f"PO #{po_id} reviewed and marked as ordered."
                    )
                    return RedirectResponse(
                        url=f"/admin/workflows/restock?step=receive&po_id={po_id}",
                        status_code=303,
                    )

                if step == "receive":
                    try:
                        po_id = int(form.get("po_id") or "")
                    except (TypeError, ValueError):
                        raise HTTPException(
                            status_code=400, detail="Select a PO"
                        ) from None
                    items = []
                    for key, value in form.multi_items():
                        if not key.startswith("qty_"):
                            continue
                        try:
                            item_id = int(key.removeprefix("qty_"))
                            qty = int(value)
                        except (TypeError, ValueError):
                            continue
                        if qty > 0:
                            items.append(
                                PurchaseOrderReceiveItem(
                                    purchase_order_item_id=item_id,
                                    quantity_received=qty,
                                )
                            )
                    if not items:
                        raise HTTPException(
                            status_code=400,
                            detail="Enter at least one received quantity",
                        )
                    try:
                        user = self._admin_user(db, request)
                        if user is None:
                            raise HTTPException(
                                status_code=403, detail="Admin user missing"
                            )
                        receive_purchase_order_items(
                            db=db,
                            current_user=user,
                            purchase_order_id=po_id,
                            receive_in=PurchaseOrderReceive(items=items),
                            tenant_id=_selected_tenant_id(request),
                        )
                    except HTTPException as exc:
                        self._flash_http_error(request, exc)
                        return RedirectResponse(
                            url="/admin/workflows/restock?step=receive", status_code=303
                        )
                    Flash.success(request, f"PO #{po_id} received — stock updated.")
                    return RedirectResponse(
                        url=f"/admin/workflows/restock?step=done&po_id={po_id}",
                        status_code=303,
                    )

            draft_pos = (
                db.query(PurchaseOrder)
                .options(
                    joinedload(PurchaseOrder.items).joinedload(
                        PurchaseOrderItem.product
                    ),
                    joinedload(PurchaseOrder.supplier),
                )
                .filter(
                    PurchaseOrder.status.in_(["draft", "ordered"]),
                    PurchaseOrder.tenant_id == _selected_tenant_id(request),
                )
                .order_by(PurchaseOrder.id.asc())
                .all()
            )
            suppliers = (
                db.query(Supplier)
                .filter(
                    Supplier.is_active.is_(True),
                    Supplier.tenant_id == _selected_tenant_id(request),
                )
                .order_by(Supplier.name.asc())
                .all()
            )
            search_q = (request.query_params.get("q") or "").strip()
            catalog_q = db.query(Product).filter(
                Product.tenant_id == _selected_tenant_id(request)
            )
            if search_q:
                like = f"%{search_q}%"
                catalog_q = catalog_q.filter(
                    (Product.name.ilike(like)) | (Product.sku.ilike(like))
                )
            catalog_products = catalog_q.order_by(Product.name.asc()).limit(50).all()
            selected_po = None
            po_id = request.query_params.get("po_id")
            if po_id:
                selected_po = next(
                    (po for po in draft_pos if po.id == int(po_id)),
                    None,
                )
            return await self.templates.TemplateResponse(
                request,
                "workflows/restock.html",
                context={
                    "title": "Restock",
                    "step": step,
                    "low_stock": low_stock,
                    "draft_pos": draft_pos,
                    "suppliers": suppliers,
                    "catalog_products": catalog_products,
                    "selected_po": selected_po,
                    "done_po_id": request.query_params.get("po_id"),
                },
            )
        except HTTPException as exc:
            self._flash_http_error(request, exc)
            return RedirectResponse(
                url="/admin/workflows/restock?step=generate", status_code=303
            )
        finally:
            db.close()

    # --------------------------------------------------------- review queue

    @expose("/workflows/review", methods=["GET", "POST"])
    async def review_workflow(self, request: Request):
        """Resolve purchase invoices and supplier payments stuck in review.

        Superuser-only by design (the panel admits only superusers): the acting
        admin user bypasses the service-layer self-approval guard, so documents
        nobody can otherwise approve get a resolution path.
        """
        db = SessionLocal()
        try:
            if request.method == "POST":
                form = await request.form()
                kind = form.get("kind")
                doc_id = form.get("id")
                action = form.get("action")
                try:
                    doc_id = int(doc_id or "")
                except (TypeError, ValueError):
                    raise HTTPException(
                        status_code=400, detail="Invalid document id"
                    ) from None
                user = self._admin_user(db, request)
                if user is None:
                    raise HTTPException(status_code=403, detail="Admin user missing")
                review_note = form.get("review_note") or None
                tenant_id = _selected_tenant_id(request)
                if kind == "invoice" and action in ("approve", "reject"):
                    action_in = PurchaseInvoiceReviewAction(review_note=review_note)
                    if action == "approve":
                        approve_purchase_invoice(
                            db=db,
                            current_user=user,
                            invoice_id=doc_id,
                            action_in=action_in,
                            tenant_id=tenant_id,
                        )
                    else:
                        reject_purchase_invoice(
                            db=db,
                            current_user=user,
                            invoice_id=doc_id,
                            action_in=action_in,
                            tenant_id=tenant_id,
                        )
                    Flash.success(request, f"Invoice #{doc_id} {action}ed.")
                elif kind == "payment" and action in ("approve", "reject"):
                    action_in = SupplierPaymentReviewAction(review_note=review_note)
                    if action == "approve":
                        approve_supplier_payment(
                            db=db,
                            current_user=user,
                            payment_id=doc_id,
                            action_in=action_in,
                            tenant_id=tenant_id,
                        )
                    else:
                        reject_supplier_payment(
                            db=db,
                            current_user=user,
                            payment_id=doc_id,
                            action_in=action_in,
                            tenant_id=tenant_id,
                        )
                    Flash.success(request, f"Payment #{doc_id} {action}ed.")
                else:
                    raise HTTPException(status_code=400, detail="Unknown review action")
                return RedirectResponse(url="/admin/workflows/review", status_code=303)

            tenant_id = _selected_tenant_id(request)
            pending_invoices = (
                db.query(PurchaseInvoice)
                .options(
                    joinedload(PurchaseInvoice.supplier),
                    joinedload(PurchaseInvoice.user),
                )
                .filter(
                    PurchaseInvoice.status == "pending_review",
                    PurchaseInvoice.tenant_id == tenant_id,
                )
                .order_by(PurchaseInvoice.id.asc())
                .all()
            )
            pending_payments = (
                db.query(SupplierPayment)
                .options(
                    joinedload(SupplierPayment.supplier),
                    joinedload(SupplierPayment.invoice),
                    joinedload(SupplierPayment.user),
                )
                .filter(
                    SupplierPayment.status == "pending_review",
                    SupplierPayment.tenant_id == tenant_id,
                )
                .order_by(SupplierPayment.id.asc())
                .all()
            )
            return await self.templates.TemplateResponse(
                request,
                "workflows/review.html",
                context={
                    "title": "Review Queue",
                    "pending_invoices": pending_invoices,
                    "pending_payments": pending_payments,
                },
            )
        except HTTPException as exc:
            self._flash_http_error(request, exc)
            return RedirectResponse(url="/admin/workflows/review", status_code=303)
        finally:
            db.close()

    # ----------------------------------------------------------- invoice flow

    @expose("/workflows/invoice", methods=["GET", "POST"])
    async def invoice_workflow(self, request: Request):
        db = SessionLocal()
        try:
            step = request.query_params.get("step", "select")
            eligible_pos = []
            pos = (
                db.query(PurchaseOrder)
                .options(
                    joinedload(PurchaseOrder.items).joinedload(
                        PurchaseOrderItem.product
                    ),
                    joinedload(PurchaseOrder.supplier),
                )
                .filter(
                    PurchaseOrder.status != "cancelled",
                    PurchaseOrder.tenant_id == _selected_tenant_id(request),
                )
                .order_by(PurchaseOrder.id.desc())
                .limit(50)
                .all()
            )
            po_item_ids = [
                item.id for po in pos for item in po.items if item.quantity_received > 0
            ]
            billed_map = self._previously_billed_map(db, po_item_ids)
            for po in pos:
                remaining = sum(
                    max(item.quantity_received - billed_map.get(item.id, 0), 0)
                    for item in po.items
                    if item.quantity_received > 0
                )
                if remaining > 0:
                    eligible_pos.append((po, remaining))

            if request.method == "POST":
                form = await request.form()
                step = form.get("step") or step
                if step == "select":
                    try:
                        po_id = int(form.get("po_id") or "")
                    except (TypeError, ValueError):
                        raise HTTPException(
                            status_code=400, detail="Select a PO"
                        ) from None
                    return RedirectResponse(
                        url=f"/admin/workflows/invoice?step=create&po_id={po_id}",
                        status_code=303,
                    )

                if step == "create":
                    po_id = int(request.query_params.get("po_id"))
                    invoice_number = (form.get("invoice_number") or "").strip()
                    if not invoice_number:
                        raise HTTPException(
                            status_code=400, detail="Invoice number is required"
                        )
                    items = []
                    for key, value in form.multi_items():
                        if key.startswith("bill_qty_"):
                            item_id = int(key.removeprefix("bill_qty_"))
                            qty = int(value or 0)
                            if qty > 0:
                                try:
                                    cost = float(form.get(f"bill_cost_{item_id}") or 0)
                                except (TypeError, ValueError):
                                    cost = 0.0
                                items.append(
                                    PurchaseInvoiceItemCreate(
                                        purchase_order_item_id=item_id,
                                        billed_quantity=qty,
                                        billed_unit_cost=cost,
                                    )
                                )
                    if not items:
                        raise HTTPException(
                            status_code=400,
                            detail="Enter at least one billed line",
                        )
                    try:
                        user = self._admin_user(db, request)
                        if user is None:
                            raise HTTPException(
                                status_code=403, detail="Admin user missing"
                            )
                        invoice = create_purchase_invoice(
                            db=db,
                            current_user=user,
                            invoice_in=PurchaseInvoiceCreate(
                                purchase_order_id=po_id,
                                invoice_number=invoice_number,
                                items=items,
                            ),
                            tenant_id=_selected_tenant_id(request),
                        )
                    except HTTPException as exc:
                        self._flash_http_error(request, exc)
                        return RedirectResponse(
                            url=f"/admin/workflows/invoice?step=create&po_id={po_id}",
                            status_code=303,
                        )
                    Flash.success(
                        request,
                        f"Invoice {invoice.invoice_number} created.",
                    )
                    return RedirectResponse(
                        url=(
                            f"/admin/workflows/invoice?step=review"
                            f"&invoice_id={invoice.id}"
                        ),
                        status_code=303,
                    )

                if step == "review":
                    invoice_id = int(request.query_params.get("invoice_id"))
                    action_name = form.get("action")
                    review_note = form.get("review_note") or None
                    try:
                        user = self._admin_user(db, request)
                        if user is None:
                            raise HTTPException(
                                status_code=403, detail="Admin user missing"
                            )
                        if action_name == "submit":
                            submit_purchase_invoice_for_review(
                                db=db,
                                current_user=user,
                                invoice_id=invoice_id,
                                action_in=PurchaseInvoiceReviewAction(
                                    review_note=review_note
                                ),
                                tenant_id=_selected_tenant_id(request),
                            )
                            Flash.success(
                                request, f"Invoice #{invoice_id} submitted for review."
                            )
                        elif action_name == "approve":
                            approve_purchase_invoice(
                                db=db,
                                current_user=user,
                                invoice_id=invoice_id,
                                action_in=PurchaseInvoiceReviewAction(
                                    review_note=review_note
                                ),
                                tenant_id=_selected_tenant_id(request),
                            )
                            Flash.success(request, f"Invoice #{invoice_id} approved.")
                        elif action_name == "reject":
                            reject_purchase_invoice(
                                db=db,
                                current_user=user,
                                invoice_id=invoice_id,
                                action_in=PurchaseInvoiceReviewAction(
                                    review_note=review_note
                                ),
                                tenant_id=_selected_tenant_id(request),
                            )
                            Flash.success(request, f"Invoice #{invoice_id} rejected.")
                        else:
                            raise HTTPException(
                                status_code=400, detail="Unknown review action"
                            )
                    except HTTPException as exc:
                        self._flash_http_error(request, exc)
                        return RedirectResponse(
                            url=(
                                f"/admin/workflows/invoice?step=review"
                                f"&invoice_id={invoice_id}"
                            ),
                            status_code=303,
                        )
                    return RedirectResponse(
                        url=f"/admin/purchase-invoice/details/{invoice_id}",
                        status_code=303,
                    )

            po_id = request.query_params.get("po_id")
            po = None
            invoice_items = []
            if po_id and step == "create":
                po = next((p for p, _ in eligible_pos if p.id == int(po_id)), None)
                if po is None:
                    po = (
                        db.query(PurchaseOrder)
                        .options(
                            joinedload(PurchaseOrder.items).joinedload(
                                PurchaseOrderItem.product
                            ),
                            joinedload(PurchaseOrder.supplier),
                        )
                        .filter(PurchaseOrder.id == int(po_id))
                        .first()
                    )
                if po is not None:
                    item_ids = [item.id for item in po.items]
                    billed_map = self._previously_billed_map(db, item_ids)
                    invoice_items = [
                        {
                            "po_item": item,
                            "remaining": max(
                                item.quantity_received - billed_map.get(item.id, 0),
                                0,
                            ),
                        }
                        for item in po.items
                        if item.quantity_received > 0
                    ]

            invoice = None
            invoice_id = request.query_params.get("invoice_id")
            if invoice_id and step == "review":
                invoice = (
                    db.query(PurchaseInvoice)
                    .options(
                        joinedload(PurchaseInvoice.items).joinedload(
                            PurchaseInvoiceItem.product
                        ),
                        joinedload(PurchaseInvoice.supplier),
                    )
                    .filter(PurchaseInvoice.id == int(invoice_id))
                    .first()
                )

            return await self.templates.TemplateResponse(
                request,
                "workflows/invoice.html",
                context={
                    "title": "Invoicing",
                    "step": step,
                    "eligible_pos": eligible_pos,
                    "po": po,
                    "invoice_items": invoice_items,
                    "invoice": invoice,
                },
            )
        except HTTPException as exc:
            self._flash_http_error(request, exc)
            return RedirectResponse(
                url="/admin/workflows/invoice?step=select", status_code=303
            )
        finally:
            db.close()

    # ------------------------------------------------------- drawer close flow

    @expose("/workflows/close-drawer", methods=["GET", "POST"])
    async def close_drawer_workflow(self, request: Request):
        db = SessionLocal()
        try:
            step = request.query_params.get("step", "select")
            open_drawers = (
                db.query(DrawerSession)
                .options(joinedload(DrawerSession.user))
                .filter(DrawerSession.status == "open")
                .order_by(DrawerSession.id.asc())
                .all()
            )

            if request.method == "POST":
                form = await request.form()
                step = form.get("step") or step
                if step == "select":
                    try:
                        drawer_id = int(form.get("drawer_id") or "")
                    except (TypeError, ValueError):
                        raise HTTPException(
                            status_code=400, detail="Select a drawer session"
                        ) from None
                    return RedirectResponse(
                        url=(
                            f"/admin/workflows/close-drawer?step=count"
                            f"&drawer_id={drawer_id}"
                        ),
                        status_code=303,
                    )

                if step == "count":
                    drawer_id = int(request.query_params.get("drawer_id"))
                    drawer = db.get(DrawerSession, drawer_id)
                    if not drawer or drawer.status != "open":
                        raise HTTPException(
                            status_code=400,
                            detail="Only open drawer sessions can be reconciled.",
                        )
                    existing = (
                        db.query(ShiftReconciliation)
                        .filter(ShiftReconciliation.drawer_session_id == drawer_id)
                        .first()
                    )
                    if existing:
                        raise HTTPException(
                            status_code=400,
                            detail="This drawer session has already been reconciled.",
                        )
                    try:
                        counted_cash = float(form.get("counted_cash") or 0)
                        counted_non_cash = form.get("counted_non_cash")
                        counted_non_cash = (
                            float(counted_non_cash) if counted_non_cash else None
                        )
                    except (TypeError, ValueError):
                        raise HTTPException(
                            status_code=400, detail="Counted cash must be a number"
                        ) from None
                    user = self._admin_user(db, request)
                    if user is None:
                        raise HTTPException(
                            status_code=403, detail="Admin user missing"
                        )
                    reconciliation = build_reconciliation(
                        db=db,
                        drawer=drawer,
                        closed_by_user_id=user.id,
                        reconcile_in=ShiftReconciliationCreate(
                            counted_cash=counted_cash,
                            counted_non_cash=counted_non_cash,
                            notes=form.get("notes") or None,
                        ),
                    )
                    db.add(reconciliation)
                    drawer.ending_cash = counted_cash
                    drawer.expected_cash = reconciliation.expected_cash
                    drawer.closed_at = datetime.now(UTC)
                    drawer.status = "closed"
                    db.add(drawer)
                    log_action(
                        db=db,
                        action="drawer.reconcile",
                        user_id=user.id,
                        resource_type="drawer_session",
                        resource_id=drawer.id,
                        details={
                            "expected_cash": str(reconciliation.expected_cash),
                            "counted_cash": str(counted_cash),
                        },
                    )
                    db.commit()
                    db.refresh(reconciliation)
                    Flash.success(request, f"Drawer #{drawer.id} closed.")
                    return RedirectResponse(
                        url=(
                            f"/admin/workflows/close-drawer?step=done"
                            f"&recon_id={reconciliation.id}"
                        ),
                        status_code=303,
                    )

            drawer = None
            totals = None
            expected_cash = None
            expected_non_cash = None
            drawer_id = request.query_params.get("drawer_id")
            if drawer_id and step == "count":
                drawer = db.get(DrawerSession, int(drawer_id))
                if drawer and drawer.status == "open":
                    totals = compute_drawer_totals(db, drawer)
                    expected_cash = float(drawer.starting_cash or 0.0)
                    expected_cash += totals["cash_sales_total"]
                    expected_cash -= totals["cash_refunds_total"]
                    expected_non_cash = totals["non_cash_sales_total"]
                    expected_non_cash -= totals["non_cash_refunds_total"]

            return await self.templates.TemplateResponse(
                request,
                "workflows/close_drawer.html",
                context={
                    "title": "Close Drawer",
                    "step": step,
                    "open_drawers": open_drawers,
                    "drawer": drawer,
                    "totals": totals,
                    "expected_cash": expected_cash,
                    "expected_non_cash": expected_non_cash,
                    "done_recon_id": request.query_params.get("recon_id"),
                },
            )
        except HTTPException as exc:
            self._flash_http_error(request, exc)
            return RedirectResponse(
                url="/admin/workflows/close-drawer?step=select", status_code=303
            )
        finally:
            db.close()

    # ------------------------------------------------------------ refund flow

    @expose("/workflows/refund", methods=["GET", "POST"])
    async def refund_workflow(self, request: Request):
        db = SessionLocal()
        try:
            step = request.query_params.get("step", "select")
            completed_orders = (
                db.query(Order)
                .options(joinedload(Order.items))
                .filter(Order.status.in_(["serving", "completed"]))
                .order_by(Order.id.desc())
                .limit(50)
                .all()
            )
            order_item_ids = [
                item.id for order in completed_orders for item in order.items
            ]
            refunded_map = self._already_refunded_map(db, order_item_ids)
            completed_order_rows = [
                {
                    "order": order,
                    "refundable_count": sum(
                        max(
                            item.quantity - refunded_map.get(item.id, 0),
                            0,
                        )
                        for item in order.items
                    ),
                }
                for order in completed_orders
            ]

            if request.method == "POST":
                form = await request.form()
                step = form.get("step") or step
                if step == "select":
                    try:
                        order_id = int(form.get("order_id") or "")
                    except (TypeError, ValueError):
                        raise HTTPException(
                            status_code=400, detail="Select an order"
                        ) from None
                    return RedirectResponse(
                        url=f"/admin/workflows/refund?step=items&order_id={order_id}",
                        status_code=303,
                    )

                if step == "items":
                    order_id = int(request.query_params.get("order_id"))
                    items = []
                    for key, value in form.multi_items():
                        if not key.startswith("refund_qty_"):
                            continue
                        try:
                            item_id = int(key.removeprefix("refund_qty_"))
                            qty = int(value)
                        except (TypeError, ValueError):
                            continue
                        if qty > 0:
                            items.append(
                                RefundItemCreate(
                                    order_item_id=item_id,
                                    quantity=qty,
                                )
                            )
                    if not items:
                        raise HTTPException(
                            status_code=400,
                            detail="Enter at least one refund quantity",
                        )
                    try:
                        user = self._admin_user(db, request)
                        if user is None:
                            raise HTTPException(
                                status_code=403, detail="Admin user missing"
                            )
                        refund = create_refund(
                            db=db,
                            current_user=user,
                            refund_in=RefundCreate(
                                order_id=order_id,
                                reason=form.get("reason") or None,
                                payment_method=(form.get("payment_method") or None),
                                idempotency_key=str(uuid4()),
                                items=items,
                            ),
                            tenant_id=_selected_tenant_id(request),
                        )
                    except HTTPException as exc:
                        self._flash_http_error(request, exc)
                        return RedirectResponse(
                            url=(
                                f"/admin/workflows/refund?step=items"
                                f"&order_id={order_id}"
                            ),
                            status_code=303,
                        )
                    Flash.success(request, f"Refund #{refund.id} recorded.")
                    return RedirectResponse(
                        url=f"/admin/workflows/refund?step=done&refund_id={refund.id}",
                        status_code=303,
                    )

            order = None
            refund_items = []
            order_id = request.query_params.get("order_id")
            if order_id and step == "items":
                order = next(
                    (o for o in completed_orders if o.id == int(order_id)),
                    None,
                )
                if order is not None:
                    item_ids = [item.id for item in order.items]
                    refunded_map = self._already_refunded_map(db, item_ids)
                    refund_items = [
                        {
                            "order_item": item,
                            "refundable": max(
                                item.quantity - refunded_map.get(item.id, 0),
                                0,
                            ),
                        }
                        for item in order.items
                    ]

            return await self.templates.TemplateResponse(
                request,
                "workflows/refund.html",
                context={
                    "title": "Refund",
                    "step": step,
                    "completed_orders": completed_order_rows,
                    "order": order,
                    "refund_items": refund_items,
                    "done_refund_id": request.query_params.get("refund_id"),
                },
            )
        except HTTPException as exc:
            self._flash_http_error(request, exc)
            return RedirectResponse(
                url="/admin/workflows/refund?step=select", status_code=303
            )
        finally:
            db.close()
