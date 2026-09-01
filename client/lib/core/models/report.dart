library;

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

  /// Per-sale COGS from the order_items.unit_cost snapshot. Lines sold
  /// before cost tracking carry no snapshot and are excluded, so
  /// [cogsKnownRatio] < 1 signals partial coverage.
  final double cogsTotal;
  final double grossMarginAmount;
  final double? grossMarginPercent;
  final double? cogsKnownRatio;

  const SalesSummary({
    required this.grossRevenue,
    required this.totalDiscounts,
    required this.totalRevenue,
    required this.totalRefunds,
    required this.netRevenue,
    required this.orderCount,
    required this.averageOrderValue,
    this.cogsTotal = 0,
    this.grossMarginAmount = 0,
    this.grossMarginPercent,
    this.cogsKnownRatio,
  });

  factory SalesSummary.fromJson(Map<String, dynamic> json) => SalesSummary(
    grossRevenue: (json['gross_revenue'] as num?)?.toDouble() ?? 0,
    totalDiscounts: (json['total_discounts'] as num?)?.toDouble() ?? 0,
    totalRevenue: (json['total_revenue'] as num?)?.toDouble() ?? 0,
    totalRefunds: (json['total_refunds'] as num?)?.toDouble() ?? 0,
    netRevenue: (json['net_revenue'] as num?)?.toDouble() ?? 0,
    orderCount: json['order_count'] as int? ?? 0,
    averageOrderValue: (json['average_order_value'] as num?)?.toDouble() ?? 0,
    cogsTotal: (json['cogs_total'] as num?)?.toDouble() ?? 0,
    grossMarginAmount:
        (json['gross_margin_amount'] as num?)?.toDouble() ?? 0,
    grossMarginPercent: (json['gross_margin_percent'] as num?)?.toDouble(),
    cogsKnownRatio: (json['cogs_known_ratio'] as num?)?.toDouble(),
  );
}
