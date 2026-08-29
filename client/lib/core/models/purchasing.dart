library;

class Supplier {
  final int id;
  final String name;
  final String? contactEmail;
  final String? phone;
  final String? address;
  final bool isActive;

  const Supplier({
    required this.id,
    required this.name,
    this.contactEmail,
    this.phone,
    this.address,
    required this.isActive,
  });

  factory Supplier.fromJson(Map<String, dynamic> json) => Supplier(
    id: json['id'] as int,
    name: json['name'] as String,
    contactEmail: json['contact_email'] as String?,
    phone: json['phone'] as String?,
    address: json['address'] as String?,
    isActive: json['is_active'] as bool? ?? true,
  );
}

class PurchaseOrderItem {
  final int id;
  final int purchaseOrderId;
  final int productId;
  final int quantityOrdered;
  final int quantityReceived;
  final double unitCost;

  const PurchaseOrderItem({
    required this.id,
    required this.purchaseOrderId,
    required this.productId,
    required this.quantityOrdered,
    required this.quantityReceived,
    required this.unitCost,
  });

  int get remaining => quantityOrdered - quantityReceived;

  factory PurchaseOrderItem.fromJson(Map<String, dynamic> json) =>
      PurchaseOrderItem(
        id: json['id'] as int,
        purchaseOrderId: json['purchase_order_id'] as int,
        productId: json['product_id'] as int,
        quantityOrdered: json['quantity_ordered'] as int,
        quantityReceived: json['quantity_received'] as int? ?? 0,
        unitCost: (json['unit_cost'] as num?)?.toDouble() ?? 0,
      );
}

class PurchaseOrder {
  final int id;
  final int supplierId;
  final int userId;
  final String status;
  final double totalEstimatedAmount;
  final String? notes;
  final String? reviewNote;
  final String? createdAt;
  final String? orderedAt;
  final String? receivedAt;
  final List<PurchaseOrderItem> items;

  const PurchaseOrder({
    required this.id,
    required this.supplierId,
    required this.userId,
    required this.status,
    required this.totalEstimatedAmount,
    this.notes,
    this.reviewNote,
    this.createdAt,
    this.orderedAt,
    this.receivedAt,
    this.items = const [],
  });

  factory PurchaseOrder.fromJson(Map<String, dynamic> json) => PurchaseOrder(
    id: json['id'] as int,
    supplierId: json['supplier_id'] as int,
    userId: json['user_id'] as int,
    status: json['status'] as String,
    totalEstimatedAmount:
        (json['total_estimated_amount'] as num?)?.toDouble() ?? 0,
    notes: json['notes'] as String?,
    reviewNote: json['review_note'] as String?,
    createdAt: json['created_at'] as String?,
    orderedAt: json['ordered_at'] as String?,
    receivedAt: json['received_at'] as String?,
    items: (json['items'] as List? ?? [])
        .map((e) => PurchaseOrderItem.fromJson(e as Map<String, dynamic>))
        .toList(),
  );
}

class PurchaseOrderItemDetail {
  final int id;
  final int purchaseOrderId;
  final int productId;
  final int quantityOrdered;
  final int quantityReceived;
  final double unitCost;
  final int quantityInvoiced;
  final double billedTotal;

  const PurchaseOrderItemDetail({
    required this.id,
    required this.purchaseOrderId,
    required this.productId,
    required this.quantityOrdered,
    required this.quantityReceived,
    required this.unitCost,
    this.quantityInvoiced = 0,
    this.billedTotal = 0,
  });

  factory PurchaseOrderItemDetail.fromJson(Map<String, dynamic> json) =>
      PurchaseOrderItemDetail(
        id: json['id'] as int,
        purchaseOrderId: json['purchase_order_id'] as int,
        productId: json['product_id'] as int,
        quantityOrdered: json['quantity_ordered'] as int,
        quantityReceived: json['quantity_received'] as int? ?? 0,
        unitCost: (json['unit_cost'] as num?)?.toDouble() ?? 0,
        quantityInvoiced: json['quantity_invoiced'] as int? ?? 0,
        billedTotal: (json['billed_total'] as num?)?.toDouble() ?? 0,
      );
}

class PurchaseOrderTimelineEvent {
  final String event;
  final String? at;
  final String? note;

  const PurchaseOrderTimelineEvent({
    required this.event,
    this.at,
    this.note,
  });

  factory PurchaseOrderTimelineEvent.fromJson(Map<String, dynamic> json) =>
      PurchaseOrderTimelineEvent(
        event: json['event'] as String,
        at: json['at'] as String?,
        note: json['note'] as String?,
      );
}

class PurchaseOrderDetail {
  final int id;
  final int supplierId;
  final int userId;
  final String status;
  final double totalEstimatedAmount;
  final String? notes;
  final String? reviewNote;
  final String? createdAt;
  final String? orderedAt;
  final String? receivedAt;
  final List<PurchaseOrderItemDetail> items;
  final List<PurchaseOrderTimelineEvent> timeline;
  final double totalReceivedAmount;
  final double totalBilledAmount;
  final double outstandingPayable;

  const PurchaseOrderDetail({
    required this.id,
    required this.supplierId,
    required this.userId,
    required this.status,
    required this.totalEstimatedAmount,
    this.notes,
    this.reviewNote,
    this.createdAt,
    this.orderedAt,
    this.receivedAt,
    this.items = const [],
    this.timeline = const [],
    this.totalReceivedAmount = 0,
    this.totalBilledAmount = 0,
    this.outstandingPayable = 0,
  });

  factory PurchaseOrderDetail.fromJson(Map<String, dynamic> json) =>
      PurchaseOrderDetail(
        id: json['id'] as int,
        supplierId: json['supplier_id'] as int,
        userId: json['user_id'] as int,
        status: json['status'] as String,
        totalEstimatedAmount:
            (json['total_estimated_amount'] as num?)?.toDouble() ?? 0,
        notes: json['notes'] as String?,
        reviewNote: json['review_note'] as String?,
        createdAt: json['created_at'] as String?,
        orderedAt: json['ordered_at'] as String?,
        receivedAt: json['received_at'] as String?,
        items: (json['items'] as List? ?? [])
            .map(
              (e) =>
                  PurchaseOrderItemDetail.fromJson(e as Map<String, dynamic>),
            )
            .toList(),
        timeline: (json['timeline'] as List? ?? [])
            .map(
              (e) =>
                  PurchaseOrderTimelineEvent.fromJson(e as Map<String, dynamic>),
            )
            .toList(),
        totalReceivedAmount:
            (json['total_received_amount'] as num?)?.toDouble() ?? 0,
        totalBilledAmount:
            (json['total_billed_amount'] as num?)?.toDouble() ?? 0,
        outstandingPayable:
            (json['outstanding_payable'] as num?)?.toDouble() ?? 0,
      );
}

class SupplierLedgerEntry {
  final String kind; // purchase_order | invoice | payment
  final int id;
  final String status;
  final double amount;
  final String? date;
  final String? reference;

  const SupplierLedgerEntry({
    required this.kind,
    required this.id,
    required this.status,
    required this.amount,
    this.date,
    this.reference,
  });

  factory SupplierLedgerEntry.fromJson(Map<String, dynamic> json) =>
      SupplierLedgerEntry(
        kind: json['kind'] as String,
        id: json['id'] as int,
        status: json['status'] as String,
        amount: (json['amount'] as num?)?.toDouble() ?? 0,
        date: json['date'] as String?,
        reference: json['reference'] as String?,
      );
}

class SupplierLedger {
  final int supplierId;
  final String supplierName;
  final int openPurchaseOrders;
  final double openPoAmount;
  final int pendingInvoiceCount;
  final double pendingInvoiceAmount;
  final double approvedInvoiceTotal;
  final double approvedPaymentTotal;
  final double outstandingPayable;
  final List<SupplierLedgerEntry> entries;

  const SupplierLedger({
    required this.supplierId,
    required this.supplierName,
    this.openPurchaseOrders = 0,
    this.openPoAmount = 0,
    this.pendingInvoiceCount = 0,
    this.pendingInvoiceAmount = 0,
    this.approvedInvoiceTotal = 0,
    this.approvedPaymentTotal = 0,
    this.outstandingPayable = 0,
    this.entries = const [],
  });

  factory SupplierLedger.fromJson(Map<String, dynamic> json) => SupplierLedger(
    supplierId: json['supplier_id'] as int,
    supplierName: json['supplier_name'] as String,
    openPurchaseOrders: json['open_purchase_orders'] as int? ?? 0,
    openPoAmount: (json['open_po_amount'] as num?)?.toDouble() ?? 0,
    pendingInvoiceCount: json['pending_invoice_count'] as int? ?? 0,
    pendingInvoiceAmount:
        (json['pending_invoice_amount'] as num?)?.toDouble() ?? 0,
    approvedInvoiceTotal:
        (json['approved_invoice_total'] as num?)?.toDouble() ?? 0,
    approvedPaymentTotal:
        (json['approved_payment_total'] as num?)?.toDouble() ?? 0,
    outstandingPayable:
        (json['outstanding_payable'] as num?)?.toDouble() ?? 0,
    entries: (json['entries'] as List? ?? [])
        .map((e) => SupplierLedgerEntry.fromJson(e as Map<String, dynamic>))
        .toList(),
  );
}

class PurchasingSettings {
  final bool autoPoEnabled;
  final int autoPoLookbackDays;
  final int autoPoMinStockTrigger;

  const PurchasingSettings({
    required this.autoPoEnabled,
    required this.autoPoLookbackDays,
    required this.autoPoMinStockTrigger,
  });

  factory PurchasingSettings.fromJson(Map<String, dynamic> json) =>
      PurchasingSettings(
        autoPoEnabled: json['auto_po_enabled'] as bool? ?? false,
        autoPoLookbackDays: json['auto_po_lookback_days'] as int? ?? 30,
        autoPoMinStockTrigger: json['auto_po_min_stock_trigger'] as int? ?? 0,
      );

  Map<String, dynamic> toJson() => {
    'auto_po_enabled': autoPoEnabled,
    'auto_po_lookback_days': autoPoLookbackDays,
    'auto_po_min_stock_trigger': autoPoMinStockTrigger,
  };
}

class SupplierSpendItem {
  final int supplierId;
  final String supplierName;
  final int poCount;
  final int invoiceCount;
  final double approvedTotal;
  final double varianceTotal;

  const SupplierSpendItem({
    required this.supplierId,
    required this.supplierName,
    this.poCount = 0,
    this.invoiceCount = 0,
    this.approvedTotal = 0,
    this.varianceTotal = 0,
  });

  factory SupplierSpendItem.fromJson(Map<String, dynamic> json) =>
      SupplierSpendItem(
        supplierId: json['supplier_id'] as int,
        supplierName: json['supplier_name'] as String,
        poCount: json['po_count'] as int? ?? 0,
        invoiceCount: json['invoice_count'] as int? ?? 0,
        approvedTotal: (json['approved_total'] as num?)?.toDouble() ?? 0,
        varianceTotal: (json['variance_total'] as num?)?.toDouble() ?? 0,
      );
}

class SupplierSpendSummary {
  final double cogsEstimate;
  final List<SupplierSpendItem> items;

  const SupplierSpendSummary({this.cogsEstimate = 0, this.items = const []});

  factory SupplierSpendSummary.fromJson(Map<String, dynamic> json) =>
      SupplierSpendSummary(
        cogsEstimate: (json['cogs_estimate'] as num?)?.toDouble() ?? 0,
        items: (json['items'] as List? ?? [])
            .map((e) => SupplierSpendItem.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class VarianceTrendItem {
  final String period;
  final int invoiceCount;
  final double billedTotal;
  final double approvedTotal;
  final double varianceTotal;

  const VarianceTrendItem({
    required this.period,
    this.invoiceCount = 0,
    this.billedTotal = 0,
    this.approvedTotal = 0,
    this.varianceTotal = 0,
  });

  factory VarianceTrendItem.fromJson(Map<String, dynamic> json) =>
      VarianceTrendItem(
        period: json['period'] as String,
        invoiceCount: json['invoice_count'] as int? ?? 0,
        billedTotal: (json['billed_total'] as num?)?.toDouble() ?? 0,
        approvedTotal: (json['approved_total'] as num?)?.toDouble() ?? 0,
        varianceTotal: (json['variance_total'] as num?)?.toDouble() ?? 0,
      );
}

class VarianceTrendSummary {
  final List<VarianceTrendItem> months;

  const VarianceTrendSummary({this.months = const []});

  factory VarianceTrendSummary.fromJson(Map<String, dynamic> json) =>
      VarianceTrendSummary(
        months: (json['months'] as List? ?? [])
            .map((e) => VarianceTrendItem.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class PurchaseInvoiceItem {
  final int id;
  final int invoiceId;
  final int purchaseOrderItemId;
  final int productId;
  final int billedQuantity;
  final double billedUnitCost;
  final int expectedQuantity;
  final double expectedUnitCost;
  final int quantityVariance;
  final double priceVariance;
  final double lineTotal;

  const PurchaseInvoiceItem({
    required this.id,
    required this.invoiceId,
    required this.purchaseOrderItemId,
    required this.productId,
    required this.billedQuantity,
    required this.billedUnitCost,
    required this.expectedQuantity,
    required this.expectedUnitCost,
    required this.quantityVariance,
    required this.priceVariance,
    required this.lineTotal,
  });

  factory PurchaseInvoiceItem.fromJson(Map<String, dynamic> json) =>
      PurchaseInvoiceItem(
        id: json['id'] as int,
        invoiceId: json['invoice_id'] as int,
        purchaseOrderItemId: json['purchase_order_item_id'] as int,
        productId: json['product_id'] as int,
        billedQuantity: json['billed_quantity'] as int,
        billedUnitCost: (json['billed_unit_cost'] as num?)?.toDouble() ?? 0,
        expectedQuantity: json['expected_quantity'] as int? ?? 0,
        expectedUnitCost:
            (json['expected_unit_cost'] as num?)?.toDouble() ?? 0,
        quantityVariance: json['quantity_variance'] as int? ?? 0,
        priceVariance: (json['price_variance'] as num?)?.toDouble() ?? 0,
        lineTotal: (json['line_total'] as num?)?.toDouble() ?? 0,
      );
}

class PurchaseInvoice {
  final int id;
  final int supplierId;
  final int purchaseOrderId;
  final int userId;
  final String invoiceNumber;
  final String status;
  final String? invoiceDate;
  final String? dueDate;
  final double subtotalAmount;
  final double totalAmount;
  final double varianceAmount;
  final bool hasQuantityVariance;
  final bool hasPriceVariance;
  final String? notes;
  final String? reviewNote;
  final String? approvedAt;
  final String? rejectedAt;
  final String? createdAt;
  final double outstandingAmount;
  final List<PurchaseInvoiceItem> items;

  const PurchaseInvoice({
    required this.id,
    required this.supplierId,
    required this.purchaseOrderId,
    required this.userId,
    required this.invoiceNumber,
    required this.status,
    this.invoiceDate,
    this.dueDate,
    required this.subtotalAmount,
    required this.totalAmount,
    required this.varianceAmount,
    required this.hasQuantityVariance,
    required this.hasPriceVariance,
    this.notes,
    this.reviewNote,
    this.approvedAt,
    this.rejectedAt,
    this.createdAt,
    this.outstandingAmount = 0,
    this.items = const [],
  });

  factory PurchaseInvoice.fromJson(Map<String, dynamic> json) =>
      PurchaseInvoice(
        id: json['id'] as int,
        supplierId: json['supplier_id'] as int,
        purchaseOrderId: json['purchase_order_id'] as int,
        userId: json['user_id'] as int,
        invoiceNumber: json['invoice_number'] as String,
        status: json['status'] as String,
        invoiceDate: json['invoice_date'] as String?,
        dueDate: json['due_date'] as String?,
        subtotalAmount: (json['subtotal_amount'] as num?)?.toDouble() ?? 0,
        totalAmount: (json['total_amount'] as num?)?.toDouble() ?? 0,
        varianceAmount: (json['variance_amount'] as num?)?.toDouble() ?? 0,
        hasQuantityVariance: json['has_quantity_variance'] as bool? ?? false,
        hasPriceVariance: json['has_price_variance'] as bool? ?? false,
        notes: json['notes'] as String?,
        reviewNote: json['review_note'] as String?,
        approvedAt: json['approved_at'] as String?,
        rejectedAt: json['rejected_at'] as String?,
        createdAt: json['created_at'] as String?,
        outstandingAmount: (json['outstanding_amount'] as num?)?.toDouble() ?? 0,
        items: (json['items'] as List? ?? [])
            .map((e) => PurchaseInvoiceItem.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class SupplierPayment {
  final int id;
  final int supplierId;
  final int invoiceId;
  final int userId;
  final double amount;
  final String paymentMethod;
  final String? reference;
  final String status;
  final String? paymentDate;
  final String? notes;
  final String? reviewNote;
  final String? approvedAt;
  final String? rejectedAt;
  final String? createdAt;

  const SupplierPayment({
    required this.id,
    required this.supplierId,
    required this.invoiceId,
    required this.userId,
    required this.amount,
    required this.paymentMethod,
    this.reference,
    required this.status,
    this.paymentDate,
    this.notes,
    this.reviewNote,
    this.approvedAt,
    this.rejectedAt,
    this.createdAt,
  });

  factory SupplierPayment.fromJson(Map<String, dynamic> json) =>
      SupplierPayment(
        id: json['id'] as int,
        supplierId: json['supplier_id'] as int,
        invoiceId: json['invoice_id'] as int,
        userId: json['user_id'] as int,
        amount: (json['amount'] as num?)?.toDouble() ?? 0,
        paymentMethod: json['payment_method'] as String,
        reference: json['reference'] as String?,
        status: json['status'] as String,
        paymentDate: json['payment_date'] as String?,
        notes: json['notes'] as String?,
        reviewNote: json['review_note'] as String?,
        approvedAt: json['approved_at'] as String?,
        rejectedAt: json['rejected_at'] as String?,
        createdAt: json['created_at'] as String?,
      );
}
