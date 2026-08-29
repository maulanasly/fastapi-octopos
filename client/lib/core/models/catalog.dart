import 'package:freezed_annotation/freezed_annotation.dart';

import 'converters.dart';

part 'catalog.freezed.dart';
part 'catalog.g.dart';

@freezed
abstract class Category with _$Category {
  const factory Category({
    required int id,
    required String name,
    String? description,
    String? color,
  }) = _Category;

  factory Category.fromJson(Map<String, dynamic> json) => _$CategoryFromJson(json);
}

@freezed
abstract class Product with _$Product {
  const Product._();

  const factory Product({
    required int id,
    required String name,
    required String sku,
    String? description,
    @JsonKey(fromJson: doubleFromJson) required double price,
    @Default(0) int stockQuantity,
    @Default(0) int minStock,
    int? maxStock,
    @Default(0) int reorderPoint,
    @Default(0) int leadTimeDays,
    int? categoryId,
    Category? category,
    String? imageUrl,
    String? thumbnailUrl,
  }) = _Product;

  factory Product.fromJson(Map<String, dynamic> json) => _$ProductFromJson(json);

  int get priceCents => (price * 100).round();

  Map<String, dynamic> toCreateJson() => {
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

@freezed
abstract class CatalogDelta with _$CatalogDelta {
  const factory CatalogDelta({
    required String serverTime,
    @Default([]) List<Category> categories,
    @Default([]) List<Product> products,
    @Default([]) List<int> deletedCategoryIds,
    @Default([]) List<int> deletedProductIds,
  }) = _CatalogDelta;

  factory CatalogDelta.fromJson(Map<String, dynamic> json) =>
      _$CatalogDeltaFromJson(json);
}
