library;


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
