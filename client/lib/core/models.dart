/// API models mirroring the backend pydantic schemas.
///
/// Amounts come from the backend as floats with 2-decimal quantization;
/// parse them with [centsFromApi] on receipt.
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

class TaxRule {
  final int id;
  final String name;
  final String? description;
  final String taxScope;
  final String taxMode;
  final double rate;
  final int? categoryId;
  final int? productId;
  final String? startsAt;
  final String? endsAt;
  final bool isActive;

  const TaxRule({
    required this.id,
    required this.name,
    this.description,
    required this.taxScope,
    required this.taxMode,
    required this.rate,
    this.categoryId,
    this.productId,
    this.startsAt,
    this.endsAt,
    required this.isActive,
  });

  factory TaxRule.fromJson(Map<String, dynamic> json) => TaxRule(
    id: json['id'] as int,
    name: json['name'] as String,
    description: json['description'] as String?,
    taxScope: json['tax_scope'] as String? ?? 'order',
    taxMode: json['tax_mode'] as String? ?? 'exclusive',
    rate: (json['rate'] as num?)?.toDouble() ?? 0,
    categoryId: json['category_id'] as int?,
    productId: json['product_id'] as int?,
    startsAt: json['starts_at'] as String?,
    endsAt: json['ends_at'] as String?,
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

class StockMovement {
  final int id;
  final int productId;
  final String movementType;
  final int quantityBefore;
  final int quantityDelta;
  final int quantityAfter;
  final String? note;
  final String? createdAt;

  const StockMovement({
    required this.id,
    required this.productId,
    required this.movementType,
    required this.quantityBefore,
    required this.quantityDelta,
    required this.quantityAfter,
    this.note,
    this.createdAt,
  });

  factory StockMovement.fromJson(Map<String, dynamic> json) => StockMovement(
    id: json['id'] as int,
    productId: json['product_id'] as int,
    movementType: json['movement_type'] as String,
    quantityBefore: json['quantity_before'] as int? ?? 0,
    quantityDelta: json['quantity_delta'] as int? ?? 0,
    quantityAfter: json['quantity_after'] as int? ?? 0,
    note: json['note'] as String?,
    createdAt: json['created_at'] as String?,
  );
}

class ReplenishmentSuggestion {
  final int productId;
  final String productName;
  final String sku;
  final int currentStock;
  final int minStock;
  final int reorderPoint;
  final int leadTimeDays;
  final int soldQuantity;
  final int projectedStockAtLeadTime;
  final int recommendedOrderQuantity;
  final bool shouldReorder;

  const ReplenishmentSuggestion({
    required this.productId,
    required this.productName,
    required this.sku,
    required this.currentStock,
    required this.minStock,
    required this.reorderPoint,
    required this.leadTimeDays,
    required this.soldQuantity,
    required this.projectedStockAtLeadTime,
    required this.recommendedOrderQuantity,
    required this.shouldReorder,
  });

  factory ReplenishmentSuggestion.fromJson(
    Map<String, dynamic> json,
  ) => ReplenishmentSuggestion(
    productId: json['product_id'] as int,
    productName: json['product_name'] as String,
    sku: json['sku'] as String,
    currentStock: json['current_stock'] as int? ?? 0,
    minStock: json['min_stock'] as int? ?? 0,
    reorderPoint: json['reorder_point'] as int? ?? 0,
    leadTimeDays: json['lead_time_days'] as int? ?? 0,
    soldQuantity: json['sold_quantity'] as int? ?? 0,
    projectedStockAtLeadTime: json['projected_stock_at_lead_time'] as int? ?? 0,
    recommendedOrderQuantity: json['recommended_order_quantity'] as int? ?? 0,
    shouldReorder: json['should_reorder'] as bool? ?? false,
  );
}

class Promotion {
  final int id;
  final String code;
  final String name;
  final String? description;
  final String discountType;
  final double discountValue;
  final double minOrderAmount;
  final double? maxDiscountAmount;
  final String appliesTo;
  final int? productId;
  final int? categoryId;
  final bool isActive;
  final int? usageLimit;
  final int usageCount;

  const Promotion({
    required this.id,
    required this.code,
    required this.name,
    this.description,
    required this.discountType,
    required this.discountValue,
    required this.minOrderAmount,
    this.maxDiscountAmount,
    required this.appliesTo,
    this.productId,
    this.categoryId,
    required this.isActive,
    this.usageLimit,
    required this.usageCount,
  });

  factory Promotion.fromJson(Map<String, dynamic> json) => Promotion(
    id: json['id'] as int,
    code: json['code'] as String,
    name: json['name'] as String,
    description: json['description'] as String?,
    discountType: json['discount_type'] as String,
    discountValue: (json['discount_value'] as num?)?.toDouble() ?? 0,
    minOrderAmount: (json['min_order_amount'] as num?)?.toDouble() ?? 0,
    maxDiscountAmount: (json['max_discount_amount'] as num?)?.toDouble(),
    appliesTo: json['applies_to'] as String? ?? 'order',
    productId: json['product_id'] as int?,
    categoryId: json['category_id'] as int?,
    isActive: json['is_active'] as bool? ?? true,
    usageLimit: json['usage_limit'] as int?,
    usageCount: json['usage_count'] as int? ?? 0,
  );
}

class AuditLogEntry {
  final int id;
  final int? userId;
  final String action;
  final String? resourceType;
  final int? resourceId;
  final String? detailsJson;
  final String? ipAddress;
  final String? requestId;
  final String? createdAt;

  const AuditLogEntry({
    required this.id,
    this.userId,
    required this.action,
    this.resourceType,
    this.resourceId,
    this.detailsJson,
    this.ipAddress,
    this.requestId,
    this.createdAt,
  });

  factory AuditLogEntry.fromJson(Map<String, dynamic> json) => AuditLogEntry(
    id: json['id'] as int,
    userId: json['user_id'] as int?,
    action: json['action'] as String,
    resourceType: json['resource_type'] as String?,
    resourceId: json['resource_id'] as int?,
    detailsJson: json['details_json'] as String?,
    ipAddress: json['ip_address'] as String?,
    requestId: json['request_id'] as String?,
    createdAt: json['created_at'] as String?,
  );
}

class PermissionInfo {
  final int id;
  final String code;
  final String? description;

  const PermissionInfo({
    required this.id,
    required this.code,
    this.description,
  });

  factory PermissionInfo.fromJson(Map<String, dynamic> json) => PermissionInfo(
    id: json['id'] as int,
    code: json['code'] as String,
    description: json['description'] as String?,
  );
}

class RoleInfo {
  final int id;
  final String name;
  final String? description;
  final bool isSystem;
  final List<String> permissions;

  const RoleInfo({
    required this.id,
    required this.name,
    this.description,
    required this.isSystem,
    this.permissions = const [],
  });

  factory RoleInfo.fromJson(Map<String, dynamic> json) => RoleInfo(
    id: json['id'] as int,
    name: json['name'] as String,
    description: json['description'] as String?,
    isSystem: json['is_system'] as bool? ?? false,
    permissions: (json['permissions'] as List? ?? [])
        .map((p) => (p as Map<String, dynamic>)['code'] as String)
        .toList(),
  );
}

class UserProfile {
  final int id;
  final String email;
  final String? fullName;
  final bool isActive;
  final bool isSuperuser;
  final int? tenantId;
  final List<String> roles;

  const UserProfile({
    required this.id,
    required this.email,
    this.fullName,
    required this.isActive,
    required this.isSuperuser,
    this.tenantId,
    this.roles = const [],
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) => UserProfile(
    id: json['id'] as int,
    email: json['email'] as String,
    fullName: json['full_name'] as String?,
    isActive: json['is_active'] as bool? ?? true,
    isSuperuser: json['is_superuser'] as bool? ?? false,
    tenantId: json['tenant_id'] as int?,
    roles: (json['roles'] as List? ?? [])
        .map((r) => (r as Map<String, dynamic>)['name'] as String)
        .toList(),
  );
}

class TokenResponse {
  final String accessToken;
  final String refreshToken;
  final String tokenType;

  const TokenResponse({
    required this.accessToken,
    required this.refreshToken,
    this.tokenType = 'bearer',
  });

  factory TokenResponse.fromJson(Map<String, dynamic> json) => TokenResponse(
    accessToken: json['access_token'] as String,
    refreshToken: json['refresh_token'] as String,
    tokenType: json['token_type'] as String? ?? 'bearer',
  );
}

class User {
  final int id;
  final String email;
  final String? fullName;
  final bool isActive;
  final bool isSuperuser;

  const User({
    required this.id,
    required this.email,
    this.fullName,
    required this.isActive,
    required this.isSuperuser,
  });

  factory User.fromJson(Map<String, dynamic> json) => User(
    id: json['id'] as int,
    email: json['email'] as String,
    fullName: json['full_name'] as String?,
    isActive: json['is_active'] as bool? ?? true,
    isSuperuser: json['is_superuser'] as bool? ?? false,
  );
}

class LocalizationSetting {
  final String language;
  final String timezone;
  final String currency;
  final String dateFormat;
  final String numberFormat;
  final String countryCode;

  const LocalizationSetting({
    required this.language,
    required this.timezone,
    required this.currency,
    required this.dateFormat,
    required this.numberFormat,
    required this.countryCode,
  });

  factory LocalizationSetting.fromJson(Map<String, dynamic> json) =>
      LocalizationSetting(
        language: json['language'] as String,
        timezone: json['timezone'] as String,
        currency: json['currency'] as String,
        dateFormat: json['date_format'] as String,
        numberFormat: json['number_format'] as String,
        countryCode: json['country_code'] as String,
      );
}

class LocalizationRegion {
  final String countryCode;
  final String language;
  final String timezone;
  final String currency;
  final String dateFormat;
  final String numberFormat;

  const LocalizationRegion({
    required this.countryCode,
    required this.language,
    required this.timezone,
    required this.currency,
    required this.dateFormat,
    required this.numberFormat,
  });

  factory LocalizationRegion.fromJson(Map<String, dynamic> json) =>
      LocalizationRegion(
        countryCode: json['country_code'] as String,
        language: json['language'] as String,
        timezone: json['timezone'] as String,
        currency: json['currency'] as String,
        dateFormat: json['date_format'] as String,
        numberFormat: json['number_format'] as String,
      );
}

/// Supported values for tenant localization settings (UI selects).
class LocalizationOptions {
  final List<String> languages;
  final List<String> currencies;
  final List<String> timezones;
  final List<String> dateFormats;
  final List<String> numberFormats;
  final List<String> countryCodes;

  const LocalizationOptions({
    required this.languages,
    required this.currencies,
    required this.timezones,
    required this.dateFormats,
    required this.numberFormats,
    required this.countryCodes,
  });

  factory LocalizationOptions.fromJson(Map<String, dynamic> json) =>
      LocalizationOptions(
        languages: (json['languages'] as List<dynamic>).cast<String>(),
        currencies: (json['currencies'] as List<dynamic>).cast<String>(),
        timezones: (json['timezones'] as List<dynamic>).cast<String>(),
        dateFormats: (json['date_formats'] as List<dynamic>).cast<String>(),
        numberFormats: (json['number_formats'] as List<dynamic>).cast<String>(),
        countryCodes: (json['country_codes'] as List<dynamic>).cast<String>(),
      );
}

class Category {
  final int id;
  final String name;
  final String? description;
  final String? color;

  const Category({
    required this.id,
    required this.name,
    this.description,
    this.color,
  });

  factory Category.fromJson(Map<String, dynamic> json) => Category(
    id: json['id'] as int,
    name: json['name'] as String,
    description: json['description'] as String?,
    color: json['color'] as String?,
  );
}

class Product {
  final int id;
  final String name;
  final String sku;
  final String? description;
  final double price;
  final int stockQuantity;
  final int minStock;
  final int? maxStock;
  final int reorderPoint;
  final int leadTimeDays;
  final int? categoryId;
  final Category? category;
  final String? imageUrl;
  final String? thumbnailUrl;

  const Product({
    required this.id,
    required this.name,
    required this.sku,
    this.description,
    required this.price,
    required this.stockQuantity,
    required this.minStock,
    this.maxStock,
    required this.reorderPoint,
    required this.leadTimeDays,
    this.categoryId,
    this.category,
    this.imageUrl,
    this.thumbnailUrl,
  });

  int get priceCents => (price * 100).round();

  factory Product.fromJson(Map<String, dynamic> json) => Product(
    id: json['id'] as int,
    name: json['name'] as String,
    sku: json['sku'] as String,
    description: json['description'] as String?,
    price: (json['price'] as num).toDouble(),
    stockQuantity: json['stock_quantity'] as int? ?? 0,
    minStock: json['min_stock'] as int? ?? 0,
    maxStock: json['max_stock'] as int?,
    reorderPoint: json['reorder_point'] as int? ?? 0,
    leadTimeDays: json['lead_time_days'] as int? ?? 0,
    categoryId: json['category_id'] as int?,
    category: json['category'] == null
        ? null
        : Category.fromJson(json['category'] as Map<String, dynamic>),
    imageUrl: json['image_url'] as String?,
    thumbnailUrl: json['thumbnail_url'] as String?,
  );

  Map<String, dynamic> toJson() => {
    'name': name,
    'sku': sku,
    'description': description,
    'price': price,
    'stock_quantity': stockQuantity,
    'min_stock': minStock,
    'max_stock': maxStock,
    'reorder_point': reorderPoint,
    'lead_time_days': leadTimeDays,
    'category_id': categoryId,
  };
}

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

class DrawerSession {
  final int id;
  final int userId;
  final double startingCash;
  final double expectedCash;
  final double? endingCash;
  final String status;
  final String? openedAt;
  final String? closedAt;

  const DrawerSession({
    required this.id,
    required this.userId,
    required this.startingCash,
    required this.expectedCash,
    this.endingCash,
    required this.status,
    this.openedAt,
    this.closedAt,
  });

  factory DrawerSession.fromJson(Map<String, dynamic> json) => DrawerSession(
    id: json['id'] as int,
    userId: json['user_id'] as int,
    startingCash: (json['starting_cash'] as num?)?.toDouble() ?? 0,
    expectedCash: (json['expected_cash'] as num?)?.toDouble() ?? 0,
    endingCash: (json['ending_cash'] as num?)?.toDouble(),
    status: json['status'] as String,
    openedAt: json['opened_at'] as String?,
    closedAt: json['closed_at'] as String?,
  );
}

class ShiftReconciliation {
  final int id;
  final int drawerSessionId;
  final int closedByUserId;
  final double cashSalesTotal;
  final double nonCashSalesTotal;
  final double refundsTotal;
  final double expectedCash;
  final double countedCash;
  final double cashVariance;
  final double expectedNonCash;
  final double countedNonCash;
  final double nonCashVariance;
  final int completedOrderCount;
  final double grossSalesTotal;
  final double netSalesTotal;

  const ShiftReconciliation({
    required this.id,
    required this.drawerSessionId,
    required this.closedByUserId,
    required this.cashSalesTotal,
    required this.nonCashSalesTotal,
    required this.refundsTotal,
    required this.expectedCash,
    required this.countedCash,
    required this.cashVariance,
    required this.expectedNonCash,
    required this.countedNonCash,
    required this.nonCashVariance,
    required this.completedOrderCount,
    required this.grossSalesTotal,
    required this.netSalesTotal,
  });

  factory ShiftReconciliation.fromJson(Map<String, dynamic> json) =>
      ShiftReconciliation(
        id: json['id'] as int,
        drawerSessionId: json['drawer_session_id'] as int,
        closedByUserId: json['closed_by_user_id'] as int? ?? 0,
        cashSalesTotal: (json['cash_sales_total'] as num?)?.toDouble() ?? 0,
        nonCashSalesTotal:
            (json['non_cash_sales_total'] as num?)?.toDouble() ?? 0,
        refundsTotal: (json['refunds_total'] as num?)?.toDouble() ?? 0,
        expectedCash: (json['expected_cash'] as num?)?.toDouble() ?? 0,
        countedCash: (json['counted_cash'] as num?)?.toDouble() ?? 0,
        cashVariance: (json['cash_variance'] as num?)?.toDouble() ?? 0,
        expectedNonCash: (json['expected_non_cash'] as num?)?.toDouble() ?? 0,
        countedNonCash: (json['counted_non_cash'] as num?)?.toDouble() ?? 0,
        nonCashVariance: (json['non_cash_variance'] as num?)?.toDouble() ?? 0,
        completedOrderCount: json['completed_order_count'] as int? ?? 0,
        grossSalesTotal: (json['gross_sales_total'] as num?)?.toDouble() ?? 0,
        netSalesTotal: (json['net_sales_total'] as num?)?.toDouble() ?? 0,
      );
}

class ShiftReport {
  final int reconciliationId;
  final int drawerSessionId;
  final String? openedAt;
  final String? closedAt;
  final String? operatorName;
  final String? closedByName;
  final double startingCash;
  final double expectedCash;
  final double countedCash;
  final double cashVariance;
  final double cashSalesTotal;
  final double nonCashSalesTotal;
  final double refundsTotal;
  final double grossSalesTotal;
  final double netSalesTotal;
  final int completedOrderCount;
  final List<PaymentBreakdownItem> paymentBreakdown;

  const ShiftReport({
    required this.reconciliationId,
    required this.drawerSessionId,
    this.openedAt,
    this.closedAt,
    this.operatorName,
    this.closedByName,
    required this.startingCash,
    required this.expectedCash,
    required this.countedCash,
    required this.cashVariance,
    required this.cashSalesTotal,
    required this.nonCashSalesTotal,
    required this.refundsTotal,
    required this.grossSalesTotal,
    required this.netSalesTotal,
    required this.completedOrderCount,
    this.paymentBreakdown = const [],
  });

  factory ShiftReport.fromJson(Map<String, dynamic> json) => ShiftReport(
    reconciliationId: json['reconciliation_id'] as int,
    drawerSessionId: json['drawer_session_id'] as int,
    openedAt: json['opened_at'] as String?,
    closedAt: json['closed_at'] as String?,
    operatorName: json['operator_name'] as String?,
    closedByName: json['closed_by_name'] as String?,
    startingCash: (json['starting_cash'] as num?)?.toDouble() ?? 0,
    expectedCash: (json['expected_cash'] as num?)?.toDouble() ?? 0,
    countedCash: (json['counted_cash'] as num?)?.toDouble() ?? 0,
    cashVariance: (json['cash_variance'] as num?)?.toDouble() ?? 0,
    cashSalesTotal: (json['cash_sales_total'] as num?)?.toDouble() ?? 0,
    nonCashSalesTotal: (json['non_cash_sales_total'] as num?)?.toDouble() ?? 0,
    refundsTotal: (json['refunds_total'] as num?)?.toDouble() ?? 0,
    grossSalesTotal: (json['gross_sales_total'] as num?)?.toDouble() ?? 0,
    netSalesTotal: (json['net_sales_total'] as num?)?.toDouble() ?? 0,
    completedOrderCount: json['completed_order_count'] as int? ?? 0,
    paymentBreakdown: (json['payment_breakdown'] as List? ?? [])
        .map((e) => PaymentBreakdownItem.fromJson(e as Map<String, dynamic>))
        .toList(),
  );
}

class PaymentBreakdownItem {
  final String paymentMethod;
  final int count;
  final double amount;

  const PaymentBreakdownItem({
    required this.paymentMethod,
    required this.count,
    required this.amount,
  });

  factory PaymentBreakdownItem.fromJson(Map<String, dynamic> json) =>
      PaymentBreakdownItem(
        paymentMethod: json['payment_method'] as String,
        count: json['count'] as int? ?? 0,
        amount: (json['amount'] as num?)?.toDouble() ?? 0,
      );
}

class DailyShiftItem {
  final int reconciliationId;
  final int drawerSessionId;
  final String? openedAt;
  final String? closedAt;
  final String? operatorName;
  final double cashSalesTotal;
  final double nonCashSalesTotal;
  final double refundsTotal;
  final double grossSalesTotal;
  final double netSalesTotal;
  final int completedOrderCount;
  final double cashVariance;

  const DailyShiftItem({
    required this.reconciliationId,
    required this.drawerSessionId,
    this.openedAt,
    this.closedAt,
    this.operatorName,
    required this.cashSalesTotal,
    required this.nonCashSalesTotal,
    required this.refundsTotal,
    required this.grossSalesTotal,
    required this.netSalesTotal,
    required this.completedOrderCount,
    required this.cashVariance,
  });

  factory DailyShiftItem.fromJson(Map<String, dynamic> json) => DailyShiftItem(
    reconciliationId: json['reconciliation_id'] as int,
    drawerSessionId: json['drawer_session_id'] as int,
    openedAt: json['opened_at'] as String?,
    closedAt: json['closed_at'] as String?,
    operatorName: json['operator_name'] as String?,
    cashSalesTotal: (json['cash_sales_total'] as num?)?.toDouble() ?? 0,
    nonCashSalesTotal: (json['non_cash_sales_total'] as num?)?.toDouble() ?? 0,
    refundsTotal: (json['refunds_total'] as num?)?.toDouble() ?? 0,
    grossSalesTotal: (json['gross_sales_total'] as num?)?.toDouble() ?? 0,
    netSalesTotal: (json['net_sales_total'] as num?)?.toDouble() ?? 0,
    completedOrderCount: json['completed_order_count'] as int? ?? 0,
    cashVariance: (json['cash_variance'] as num?)?.toDouble() ?? 0,
  );
}

class DailyCloseTotals {
  final double grossSalesTotal;
  final double netSalesTotal;
  final double cashSalesTotal;
  final double nonCashSalesTotal;
  final double refundsTotal;
  final double cashVariance;
  final double nonCashVariance;
  final int completedOrderCount;
  final int shiftCount;

  const DailyCloseTotals({
    required this.grossSalesTotal,
    required this.netSalesTotal,
    required this.cashSalesTotal,
    required this.nonCashSalesTotal,
    required this.refundsTotal,
    required this.cashVariance,
    required this.nonCashVariance,
    required this.completedOrderCount,
    required this.shiftCount,
  });

  factory DailyCloseTotals.fromJson(Map<String, dynamic> json) =>
      DailyCloseTotals(
        grossSalesTotal: (json['gross_sales_total'] as num?)?.toDouble() ?? 0,
        netSalesTotal: (json['net_sales_total'] as num?)?.toDouble() ?? 0,
        cashSalesTotal: (json['cash_sales_total'] as num?)?.toDouble() ?? 0,
        nonCashSalesTotal:
            (json['non_cash_sales_total'] as num?)?.toDouble() ?? 0,
        refundsTotal: (json['refunds_total'] as num?)?.toDouble() ?? 0,
        cashVariance: (json['cash_variance'] as num?)?.toDouble() ?? 0,
        nonCashVariance: (json['non_cash_variance'] as num?)?.toDouble() ?? 0,
        completedOrderCount: json['completed_order_count'] as int? ?? 0,
        shiftCount: json['shift_count'] as int? ?? 0,
      );
}

class TopProductItem {
  final int productId;
  final String productName;
  final String productSku;
  final int totalQuantitySold;
  final double totalRevenue;

  const TopProductItem({
    required this.productId,
    required this.productName,
    required this.productSku,
    required this.totalQuantitySold,
    required this.totalRevenue,
  });

  factory TopProductItem.fromJson(Map<String, dynamic> json) => TopProductItem(
    productId: json['product_id'] as int,
    productName: json['product_name'] as String,
    productSku: json['product_sku'] as String,
    totalQuantitySold: json['total_quantity_sold'] as int? ?? 0,
    totalRevenue: (json['total_revenue'] as num?)?.toDouble() ?? 0,
  );
}

class CategorySalesItem {
  final int categoryId;
  final String categoryName;
  final double totalRevenue;
  final int totalQuantitySold;

  const CategorySalesItem({
    required this.categoryId,
    required this.categoryName,
    required this.totalRevenue,
    required this.totalQuantitySold,
  });

  factory CategorySalesItem.fromJson(Map<String, dynamic> json) =>
      CategorySalesItem(
        categoryId: json['category_id'] as int,
        categoryName: json['category_name'] as String,
        totalRevenue: (json['total_revenue'] as num?)?.toDouble() ?? 0,
        totalQuantitySold: json['total_quantity_sold'] as int? ?? 0,
      );
}

class SalesSummary {
  final double grossRevenue;
  final double totalDiscounts;
  final double totalRevenue;
  final double totalRefunds;
  final double netRevenue;
  final int orderCount;
  final double averageOrderValue;

  const SalesSummary({
    required this.grossRevenue,
    required this.totalDiscounts,
    required this.totalRevenue,
    required this.totalRefunds,
    required this.netRevenue,
    required this.orderCount,
    required this.averageOrderValue,
  });

  factory SalesSummary.fromJson(Map<String, dynamic> json) => SalesSummary(
    grossRevenue: (json['gross_revenue'] as num?)?.toDouble() ?? 0,
    totalDiscounts: (json['total_discounts'] as num?)?.toDouble() ?? 0,
    totalRevenue: (json['total_revenue'] as num?)?.toDouble() ?? 0,
    totalRefunds: (json['total_refunds'] as num?)?.toDouble() ?? 0,
    netRevenue: (json['net_revenue'] as num?)?.toDouble() ?? 0,
    orderCount: json['order_count'] as int? ?? 0,
    averageOrderValue: (json['average_order_value'] as num?)?.toDouble() ?? 0,
  );
}

class CatalogDelta {
  final String serverTime;
  final List<Category> categories;
  final List<Product> products;

  const CatalogDelta({
    required this.serverTime,
    this.categories = const [],
    this.products = const [],
  });

  factory CatalogDelta.fromJson(Map<String, dynamic> json) => CatalogDelta(
    serverTime: json['server_time'] as String,
    categories: (json['categories'] as List? ?? [])
        .map((e) => Category.fromJson(e as Map<String, dynamic>))
        .toList(),
    products: (json['products'] as List? ?? [])
        .map((e) => Product.fromJson(e as Map<String, dynamic>))
        .toList(),
  );
}
