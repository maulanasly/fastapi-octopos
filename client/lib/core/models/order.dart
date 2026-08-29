library;

import 'catalog.dart';

class Customer {
  final int id;
  final String name;
  final String? email;
  final String? phone;
  final bool isActive;
  final int pointsBalance;

  const Customer({
    required this.id,
    required this.name,
    this.email,
    this.phone,
    required this.isActive,
    required this.pointsBalance,
  });

  factory Customer.fromJson(Map<String, dynamic> json) => Customer(
    id: json['id'] as int,
    name: json['name'] as String,
    email: json['email'] as String?,
    phone: json['phone'] as String?,
    isActive: json['is_active'] as bool? ?? true,
    pointsBalance: json['points_balance'] as int? ?? 0,
  );
}

class PaymentLine {
  final int id;
  final int orderId;
  final String paymentMethod;
  final double amount;
  final int userId;

  const PaymentLine({
    required this.id,
    required this.orderId,
    required this.paymentMethod,
    required this.amount,
    required this.userId,
  });

  factory PaymentLine.fromJson(Map<String, dynamic> json) => PaymentLine(
    id: json['id'] as int,
    orderId: json['order_id'] as int,
    paymentMethod: json['payment_method'] as String,
    amount: (json['amount'] as num).toDouble(),
    userId: json['user_id'] as int? ?? 0,
  );
}

class TaxLine {
  final String taxName;
  final String taxScope;
  final double taxRate;
  final double taxableBase;
  final double taxAmount;

  const TaxLine({
    required this.taxName,
    required this.taxScope,
    required this.taxRate,
    required this.taxableBase,
    required this.taxAmount,
  });

  factory TaxLine.fromJson(Map<String, dynamic> json) => TaxLine(
    taxName: json['tax_name'] as String,
    taxScope: json['tax_scope'] as String? ?? 'order',
    taxRate: (json['tax_rate'] as num?)?.toDouble() ?? 0,
    taxableBase: (json['taxable_base'] as num?)?.toDouble() ?? 0,
    taxAmount: (json['tax_amount'] as num?)?.toDouble() ?? 0,
  );
}

class OrderItem {
  final int id;
  final int orderId;
  final int productId;
  final int quantity;
  final double unitPrice;
  final Product? product;

  const OrderItem({
    required this.id,
    required this.orderId,
    required this.productId,
    required this.quantity,
    required this.unitPrice,
    this.product,
  });

  factory OrderItem.fromJson(Map<String, dynamic> json) => OrderItem(
    id: json['id'] as int,
    orderId: json['order_id'] as int,
    productId: json['product_id'] as int,
    quantity: json['quantity'] as int,
    unitPrice: (json['unit_price'] as num).toDouble(),
    product: json['product'] == null
        ? null
        : Product.fromJson(json['product'] as Map<String, dynamic>),
  );
}

/// A single location ping for a tracked order.

class LocationUpdate {
  final double lat;
  final double lng;
  final String source;
  final String? createdAt;

  const LocationUpdate({
    required this.lat,
    required this.lng,
    this.source = 'gps',
    this.createdAt,
  });

  factory LocationUpdate.fromJson(Map<String, dynamic> json) => LocationUpdate(
    lat: (json['lat'] as num).toDouble(),
    lng: (json['lng'] as num).toDouble(),
    source: json['source'] as String? ?? 'gps',
    createdAt: json['created_at'] as String?,
  );
}

/// Lightweight order-tracking view returned by `/orders/tracking/`.

class TrackedOrder {
  final int orderId;
  final String status;
  final String trackingStatus;
  final String? destinationAddress;
  final double? destinationLat;
  final double? destinationLng;
  final LocationUpdate? latestLocation;
  final String? createdAt;

  const TrackedOrder({
    required this.orderId,
    required this.status,
    required this.trackingStatus,
    this.destinationAddress,
    this.destinationLat,
    this.destinationLng,
    this.latestLocation,
    this.createdAt,
  });

  factory TrackedOrder.fromJson(Map<String, dynamic> json) => TrackedOrder(
    orderId: json['order_id'] as int,
    status: json['status'] as String,
    trackingStatus: json['tracking_status'] as String? ?? 'none',
    destinationAddress: json['destination_address'] as String?,
    destinationLat: (json['destination_lat'] as num?)?.toDouble(),
    destinationLng: (json['destination_lng'] as num?)?.toDouble(),
    latestLocation: json['latest_location'] == null
        ? null
        : LocationUpdate.fromJson(json['latest_location'] as Map<String, dynamic>),
    createdAt: json['created_at'] as String?,
  );
}

class Order {
  final int id;
  final int userId;
  final int? drawerSessionId;
  final String? idempotencyKey;
  final double subtotalAmount;
  final double discountAmount;
  final double taxableBaseAmount;
  final double taxTotalAmount;
  final double grandTotalAmount;
  final double totalAmount;
  final double paidAmount;
  final double changeAmount;
  final double remainingAmount;
  final int redeemedPoints;
  final String status;
  final String servingStatus;
  final String? preparingAt;
  final String? readyAt;
  final String? servedAt;
  final String reservationStatus;
  final String? destinationAddress;
  final double? destinationLat;
  final double? destinationLng;
  final String trackingStatus;
  final String? assignedAt;
  final String? enRouteAt;
  final String? onSiteAt;
  final LocationUpdate? latestLocation;
  final String? createdAt;
  final List<OrderItem> items;
  final List<PaymentLine> payments;
  final List<TaxLine> taxLines;
  final Customer? customer;

  const Order({
    required this.id,
    required this.userId,
    this.drawerSessionId,
    this.idempotencyKey,
    required this.subtotalAmount,
    required this.discountAmount,
    required this.taxableBaseAmount,
    required this.taxTotalAmount,
    required this.grandTotalAmount,
    required this.totalAmount,
    required this.paidAmount,
    required this.changeAmount,
    required this.remainingAmount,
    required this.redeemedPoints,
    required this.status,
    this.servingStatus = 'none',
    this.preparingAt,
    this.readyAt,
    this.servedAt,
    required this.reservationStatus,
    this.destinationAddress,
    this.destinationLat,
    this.destinationLng,
    this.trackingStatus = 'none',
    this.assignedAt,
    this.enRouteAt,
    this.onSiteAt,
    this.latestLocation,
    this.createdAt,
    this.items = const [],
    this.payments = const [],
    this.taxLines = const [],
    this.customer,
  });

  factory Order.fromJson(Map<String, dynamic> json) => Order(
    id: json['id'] as int,
    userId: json['user_id'] as int,
    drawerSessionId: json['drawer_session_id'] as int?,
    idempotencyKey: json['idempotency_key'] as String?,
    subtotalAmount: (json['subtotal_amount'] as num?)?.toDouble() ?? 0,
    discountAmount: (json['discount_amount'] as num?)?.toDouble() ?? 0,
    taxableBaseAmount: (json['taxable_base_amount'] as num?)?.toDouble() ?? 0,
    taxTotalAmount: (json['tax_total_amount'] as num?)?.toDouble() ?? 0,
    grandTotalAmount: (json['grand_total_amount'] as num?)?.toDouble() ?? 0,
    totalAmount: (json['total_amount'] as num?)?.toDouble() ?? 0,
    paidAmount: (json['paid_amount'] as num?)?.toDouble() ?? 0,
    changeAmount: (json['change_amount'] as num?)?.toDouble() ?? 0,
    remainingAmount: (json['remaining_amount'] as num?)?.toDouble() ?? 0,
    redeemedPoints: json['redeemed_points'] as int? ?? 0,
    status: json['status'] as String,
    servingStatus: json['serving_status'] as String? ?? 'none',
    preparingAt: json['preparing_at'] as String?,
    readyAt: json['ready_at'] as String?,
    servedAt: json['served_at'] as String?,
    reservationStatus: json['reservation_status'] as String? ?? '',
    destinationAddress: json['destination_address'] as String?,
    destinationLat: (json['destination_lat'] as num?)?.toDouble(),
    destinationLng: (json['destination_lng'] as num?)?.toDouble(),
    trackingStatus: json['tracking_status'] as String? ?? 'none',
    assignedAt: json['assigned_at'] as String?,
    enRouteAt: json['en_route_at'] as String?,
    onSiteAt: json['on_site_at'] as String?,
    latestLocation: json['latest_location'] == null
        ? null
        : LocationUpdate.fromJson(json['latest_location'] as Map<String, dynamic>),
    items: (json['items'] as List? ?? [])
        .map((e) => OrderItem.fromJson(e as Map<String, dynamic>))
        .toList(),
    payments: (json['payments'] as List? ?? [])
        .map((e) => PaymentLine.fromJson(e as Map<String, dynamic>))
        .toList(),
    taxLines: (json['tax_lines'] as List? ?? [])
        .map((e) => TaxLine.fromJson(e as Map<String, dynamic>))
        .toList(),
    customer: json['customer'] == null
        ? null
        : Customer.fromJson(json['customer'] as Map<String, dynamic>),
  );
}

class ReceiptItem {
  final int productId;
  final int quantity;
  final double unitPrice;
  final double lineTotal;

  const ReceiptItem({
    required this.productId,
    required this.quantity,
    required this.unitPrice,
    required this.lineTotal,
  });

  factory ReceiptItem.fromJson(Map<String, dynamic> json) => ReceiptItem(
    productId: json['product_id'] as int,
    quantity: json['quantity'] as int,
    unitPrice: (json['unit_price'] as num).toDouble(),
    lineTotal: (json['line_total'] as num).toDouble(),
  );
}

class OrderReceipt {
  final int orderId;
  final String? customerName;
  final String? cashierName;
  final String? createdAt;
  final double subtotalAmount;
  final double discountAmount;
  final int redeemedPoints;
  final double taxableBaseAmount;
  final double taxTotalAmount;
  final double grandTotalAmount;
  final double totalAmount;
  final double paidAmount;
  final double changeAmount;
  final double remainingAmount;
  final String status;
  final String servingStatus;
  final String reservationStatus;
  final List<ReceiptItem> items;
  final List<TaxLine> taxLines;
  final List<PaymentLine> payments;

  const OrderReceipt({
    required this.orderId,
    this.customerName,
    this.cashierName,
    this.createdAt,
    required this.subtotalAmount,
    required this.discountAmount,
    required this.redeemedPoints,
    required this.taxableBaseAmount,
    required this.taxTotalAmount,
    required this.grandTotalAmount,
    required this.totalAmount,
    required this.paidAmount,
    required this.changeAmount,
    required this.remainingAmount,
    required this.status,
    this.servingStatus = 'none',
    required this.reservationStatus,
    this.items = const [],
    this.taxLines = const [],
    this.payments = const [],
  });

  factory OrderReceipt.fromJson(Map<String, dynamic> json) => OrderReceipt(
    orderId: json['order_id'] as int,
    subtotalAmount: (json['subtotal_amount'] as num?)?.toDouble() ?? 0,
    discountAmount: (json['discount_amount'] as num?)?.toDouble() ?? 0,
    redeemedPoints: json['redeemed_points'] as int? ?? 0,
    taxableBaseAmount: (json['taxable_base_amount'] as num?)?.toDouble() ?? 0,
    taxTotalAmount: (json['tax_total_amount'] as num?)?.toDouble() ?? 0,
    grandTotalAmount: (json['grand_total_amount'] as num?)?.toDouble() ?? 0,
    totalAmount: (json['total_amount'] as num?)?.toDouble() ?? 0,
    paidAmount: (json['paid_amount'] as num?)?.toDouble() ?? 0,
    changeAmount: (json['change_amount'] as num?)?.toDouble() ?? 0,
    remainingAmount: (json['remaining_amount'] as num?)?.toDouble() ?? 0,
    status: json['status'] as String,
    servingStatus: json['serving_status'] as String? ?? 'none',
    reservationStatus: json['reservation_status'] as String? ?? '',
    items: (json['items'] as List? ?? [])
        .map((e) => ReceiptItem.fromJson(e as Map<String, dynamic>))
        .toList(),
    taxLines: (json['tax_lines'] as List? ?? [])
        .map((e) => TaxLine.fromJson(e as Map<String, dynamic>))
        .toList(),
    payments: (json['payments'] as List? ?? [])
        .map((e) => PaymentLine.fromJson(e as Map<String, dynamic>))
        .toList(),
  );
}

class RefundItem {
  final int id;
  final int refundId;
  final int orderItemId;
  final int productId;
  final int quantity;
  final double unitPrice;

  const RefundItem({
    required this.id,
    required this.refundId,
    required this.orderItemId,
    required this.productId,
    required this.quantity,
    required this.unitPrice,
  });

  factory RefundItem.fromJson(Map<String, dynamic> json) => RefundItem(
    id: json['id'] as int,
    refundId: json['refund_id'] as int,
    orderItemId: json['order_item_id'] as int,
    productId: json['product_id'] as int,
    quantity: json['quantity'] as int,
    unitPrice: (json['unit_price'] as num).toDouble(),
  );
}

class Refund {
  final int id;
  final int orderId;
  final int userId;
  final String? reason;
  final String? idempotencyKey;
  final String? paymentMethod;
  final double totalAmount;
  final List<RefundItem> items;

  const Refund({
    required this.id,
    required this.orderId,
    required this.userId,
    this.reason,
    this.idempotencyKey,
    this.paymentMethod,
    required this.totalAmount,
    this.items = const [],
  });

  factory Refund.fromJson(Map<String, dynamic> json) => Refund(
    id: json['id'] as int,
    orderId: json['order_id'] as int,
    userId: json['user_id'] as int,
    reason: json['reason'] as String?,
    idempotencyKey: json['idempotency_key'] as String?,
    paymentMethod: json['payment_method'] as String?,
    totalAmount: (json['total_amount'] as num).toDouble(),
    items: (json['items'] as List? ?? [])
        .map((e) => RefundItem.fromJson(e as Map<String, dynamic>))
        .toList(),
  );
}
