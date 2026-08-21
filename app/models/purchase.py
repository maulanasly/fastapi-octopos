from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    contact_email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant")
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    supplier_id = Column(
        Integer, ForeignKey("suppliers.id"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(
        String, nullable=False, default="draft", index=True
    )  # draft, pending_review, ordered, partially_received, received, cancelled, rejected
    total_estimated_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    notes = Column(Text, nullable=True)
    review_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    ordered_at = Column(DateTime(timezone=True), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)

    tenant = relationship("Tenant")
    supplier = relationship("Supplier", back_populates="purchase_orders")
    user = relationship("User")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order")
    invoices = relationship("PurchaseInvoice", back_populates="purchase_order")


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    purchase_order_id = Column(
        Integer, ForeignKey("purchase_orders.id"), nullable=False, index=True
    )
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    quantity_ordered = Column(Integer, nullable=False)
    quantity_received = Column(Integer, nullable=False, default=0)
    unit_cost = Column(Numeric(12, 2), nullable=False)

    tenant = relationship("Tenant")
    purchase_order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product")
    invoice_items = relationship(
        "PurchaseInvoiceItem", back_populates="purchase_order_item"
    )


class PurchaseInvoice(Base):
    __tablename__ = "purchase_invoices"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    supplier_id = Column(
        Integer, ForeignKey("suppliers.id"), nullable=False, index=True
    )
    purchase_order_id = Column(
        Integer, ForeignKey("purchase_orders.id"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    invoice_number = Column(String, nullable=False, index=True)
    status = Column(
        String, nullable=False, default="draft", index=True
    )  # draft, pending_review, approved, rejected
    invoice_date = Column(DateTime(timezone=True), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    subtotal_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    variance_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    has_quantity_variance = Column(Boolean, nullable=False, default=False)
    has_price_variance = Column(Boolean, nullable=False, default=False)
    notes = Column(Text, nullable=True)
    review_note = Column(Text, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant")
    supplier = relationship("Supplier")
    purchase_order = relationship("PurchaseOrder", back_populates="invoices")
    user = relationship("User")
    items = relationship("PurchaseInvoiceItem", back_populates="invoice")


class PurchaseInvoiceItem(Base):
    __tablename__ = "purchase_invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    invoice_id = Column(
        Integer, ForeignKey("purchase_invoices.id"), nullable=False, index=True
    )
    purchase_order_item_id = Column(
        Integer, ForeignKey("purchase_order_items.id"), nullable=False, index=True
    )
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    billed_quantity = Column(Integer, nullable=False)
    billed_unit_cost = Column(Numeric(12, 2), nullable=False)
    expected_quantity = Column(Integer, nullable=False)
    expected_unit_cost = Column(Numeric(12, 2), nullable=False)
    quantity_variance = Column(Integer, nullable=False, default=0)
    price_variance = Column(Numeric(12, 2), nullable=False, default=0.0)
    line_total = Column(Numeric(12, 2), nullable=False, default=0.0)

    tenant = relationship("Tenant")
    invoice = relationship("PurchaseInvoice", back_populates="items")
    purchase_order_item = relationship(
        "PurchaseOrderItem", back_populates="invoice_items"
    )
    product = relationship("Product")


class SupplierPayment(Base):
    __tablename__ = "supplier_payments"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    supplier_id = Column(
        Integer, ForeignKey("suppliers.id"), nullable=False, index=True
    )
    invoice_id = Column(
        Integer, ForeignKey("purchase_invoices.id"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(String, nullable=False)  # e.g. "cash", "transfer", "card"
    reference = Column(String, nullable=True)
    status = Column(
        String, nullable=False, default="draft", index=True
    )  # draft, pending_review, approved, rejected
    payment_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    review_note = Column(Text, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant")
    supplier = relationship("Supplier")
    invoice = relationship("PurchaseInvoice")
    user = relationship("User")
