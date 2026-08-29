library;

import 'purchasing.dart';

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
  final double unitCost;
  final int? suggestedSupplierId;
  final String? suggestedSupplierName;

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
    this.unitCost = 0,
    this.suggestedSupplierId,
    this.suggestedSupplierName,
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
    unitCost: (json['unit_cost'] as num?)?.toDouble() ?? 0,
    suggestedSupplierId: json['suggested_supplier_id'] as int?,
    suggestedSupplierName: json['suggested_supplier_name'] as String?,
  );
}

class SkippedProduct {
  final int productId;
  final String reason;

  const SkippedProduct({required this.productId, required this.reason});

  factory SkippedProduct.fromJson(Map<String, dynamic> json) => SkippedProduct(
    productId: json['product_id'] as int,
    reason: json['reason'] as String? ?? '',
  );
}

class BatchReplenishmentResult {
  final List<PurchaseOrder> purchaseOrders;
  final List<SkippedProduct> skipped;

  const BatchReplenishmentResult({
    required this.purchaseOrders,
    required this.skipped,
  });
}
