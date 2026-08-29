// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'catalog.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_Category _$CategoryFromJson(Map<String, dynamic> json) =>
    $checkedCreate('_Category', json, ($checkedConvert) {
      final val = _Category(
        id: $checkedConvert('id', (v) => (v as num).toInt()),
        name: $checkedConvert('name', (v) => v as String),
        description: $checkedConvert('description', (v) => v as String?),
        color: $checkedConvert('color', (v) => v as String?),
      );
      return val;
    });

Map<String, dynamic> _$CategoryToJson(_Category instance) => <String, dynamic>{
  'id': instance.id,
  'name': instance.name,
  'description': ?instance.description,
  'color': ?instance.color,
};

_Product _$ProductFromJson(Map<String, dynamic> json) => $checkedCreate(
  '_Product',
  json,
  ($checkedConvert) {
    final val = _Product(
      id: $checkedConvert('id', (v) => (v as num).toInt()),
      name: $checkedConvert('name', (v) => v as String),
      sku: $checkedConvert('sku', (v) => v as String),
      description: $checkedConvert('description', (v) => v as String?),
      price: $checkedConvert('price', (v) => doubleFromJson(v)),
      stockQuantity: $checkedConvert(
        'stock_quantity',
        (v) => (v as num?)?.toInt() ?? 0,
      ),
      minStock: $checkedConvert('min_stock', (v) => (v as num?)?.toInt() ?? 0),
      maxStock: $checkedConvert('max_stock', (v) => (v as num?)?.toInt()),
      reorderPoint: $checkedConvert(
        'reorder_point',
        (v) => (v as num?)?.toInt() ?? 0,
      ),
      leadTimeDays: $checkedConvert(
        'lead_time_days',
        (v) => (v as num?)?.toInt() ?? 0,
      ),
      categoryId: $checkedConvert('category_id', (v) => (v as num?)?.toInt()),
      category: $checkedConvert(
        'category',
        (v) => v == null ? null : Category.fromJson(v as Map<String, dynamic>),
      ),
      imageUrl: $checkedConvert('image_url', (v) => v as String?),
      thumbnailUrl: $checkedConvert('thumbnail_url', (v) => v as String?),
    );
    return val;
  },
  fieldKeyMap: const {
    'stockQuantity': 'stock_quantity',
    'minStock': 'min_stock',
    'maxStock': 'max_stock',
    'reorderPoint': 'reorder_point',
    'leadTimeDays': 'lead_time_days',
    'categoryId': 'category_id',
    'imageUrl': 'image_url',
    'thumbnailUrl': 'thumbnail_url',
  },
);

Map<String, dynamic> _$ProductToJson(_Product instance) => <String, dynamic>{
  'id': instance.id,
  'name': instance.name,
  'sku': instance.sku,
  'description': ?instance.description,
  'price': instance.price,
  'stock_quantity': instance.stockQuantity,
  'min_stock': instance.minStock,
  'max_stock': ?instance.maxStock,
  'reorder_point': instance.reorderPoint,
  'lead_time_days': instance.leadTimeDays,
  'category_id': ?instance.categoryId,
  'category': ?instance.category?.toJson(),
  'image_url': ?instance.imageUrl,
  'thumbnail_url': ?instance.thumbnailUrl,
};

_CatalogDelta _$CatalogDeltaFromJson(
  Map<String, dynamic> json,
) => $checkedCreate(
  '_CatalogDelta',
  json,
  ($checkedConvert) {
    final val = _CatalogDelta(
      serverTime: $checkedConvert('server_time', (v) => v as String),
      categories: $checkedConvert(
        'categories',
        (v) =>
            (v as List<dynamic>?)
                ?.map((e) => Category.fromJson(e as Map<String, dynamic>))
                .toList() ??
            const [],
      ),
      products: $checkedConvert(
        'products',
        (v) =>
            (v as List<dynamic>?)
                ?.map((e) => Product.fromJson(e as Map<String, dynamic>))
                .toList() ??
            const [],
      ),
      deletedCategoryIds: $checkedConvert(
        'deleted_category_ids',
        (v) =>
            (v as List<dynamic>?)?.map((e) => (e as num).toInt()).toList() ??
            const [],
      ),
      deletedProductIds: $checkedConvert(
        'deleted_product_ids',
        (v) =>
            (v as List<dynamic>?)?.map((e) => (e as num).toInt()).toList() ??
            const [],
      ),
    );
    return val;
  },
  fieldKeyMap: const {
    'serverTime': 'server_time',
    'deletedCategoryIds': 'deleted_category_ids',
    'deletedProductIds': 'deleted_product_ids',
  },
);

Map<String, dynamic> _$CatalogDeltaToJson(_CatalogDelta instance) =>
    <String, dynamic>{
      'server_time': instance.serverTime,
      'categories': instance.categories.map((e) => e.toJson()).toList(),
      'products': instance.products.map((e) => e.toJson()).toList(),
      'deleted_category_ids': instance.deletedCategoryIds,
      'deleted_product_ids': instance.deletedProductIds,
    };
