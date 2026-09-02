// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'catalog.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$Category {

 int get id; String get name; String? get description; String? get color;
/// Create a copy of Category
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$CategoryCopyWith<Category> get copyWith => _$CategoryCopyWithImpl<Category>(this as Category, _$identity);

  /// Serializes this Category to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is Category&&(identical(other.id, id) || other.id == id)&&(identical(other.name, name) || other.name == name)&&(identical(other.description, description) || other.description == description)&&(identical(other.color, color) || other.color == color));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,name,description,color);

@override
String toString() {
  return 'Category(id: $id, name: $name, description: $description, color: $color)';
}


}

/// @nodoc
abstract mixin class $CategoryCopyWith<$Res>  {
  factory $CategoryCopyWith(Category value, $Res Function(Category) _then) = _$CategoryCopyWithImpl;
@useResult
$Res call({
 int id, String name, String? description, String? color
});




}
/// @nodoc
class _$CategoryCopyWithImpl<$Res>
    implements $CategoryCopyWith<$Res> {
  _$CategoryCopyWithImpl(this._self, this._then);

  final Category _self;
  final $Res Function(Category) _then;

/// Create a copy of Category
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? id = null,Object? name = null,Object? description = freezed,Object? color = freezed,}) {
  return _then(_self.copyWith(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as int,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,color: freezed == color ? _self.color : color // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [Category].
extension CategoryPatterns on Category {
/// A variant of `map` that fallback to returning `orElse`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _Category value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _Category() when $default != null:
return $default(_that);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// Callbacks receives the raw object, upcasted.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case final Subclass2 value:
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _Category value)  $default,){
final _that = this;
switch (_that) {
case _Category():
return $default(_that);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `map` that fallback to returning `null`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _Category value)?  $default,){
final _that = this;
switch (_that) {
case _Category() when $default != null:
return $default(_that);case _:
  return null;

}
}
/// A variant of `when` that fallback to an `orElse` callback.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( int id,  String name,  String? description,  String? color)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _Category() when $default != null:
return $default(_that.id,_that.name,_that.description,_that.color);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// As opposed to `map`, this offers destructuring.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case Subclass2(:final field2):
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( int id,  String name,  String? description,  String? color)  $default,) {final _that = this;
switch (_that) {
case _Category():
return $default(_that.id,_that.name,_that.description,_that.color);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `when` that fallback to returning `null`
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( int id,  String name,  String? description,  String? color)?  $default,) {final _that = this;
switch (_that) {
case _Category() when $default != null:
return $default(_that.id,_that.name,_that.description,_that.color);case _:
  return null;

}
}

}

/// @nodoc
@JsonSerializable()

class _Category implements Category {
  const _Category({required this.id, required this.name, this.description, this.color});
  factory _Category.fromJson(Map<String, dynamic> json) => _$CategoryFromJson(json);

@override final  int id;
@override final  String name;
@override final  String? description;
@override final  String? color;

/// Create a copy of Category
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$CategoryCopyWith<_Category> get copyWith => __$CategoryCopyWithImpl<_Category>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$CategoryToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _Category&&(identical(other.id, id) || other.id == id)&&(identical(other.name, name) || other.name == name)&&(identical(other.description, description) || other.description == description)&&(identical(other.color, color) || other.color == color));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,name,description,color);

@override
String toString() {
  return 'Category(id: $id, name: $name, description: $description, color: $color)';
}


}

/// @nodoc
abstract mixin class _$CategoryCopyWith<$Res> implements $CategoryCopyWith<$Res> {
  factory _$CategoryCopyWith(_Category value, $Res Function(_Category) _then) = __$CategoryCopyWithImpl;
@override @useResult
$Res call({
 int id, String name, String? description, String? color
});




}
/// @nodoc
class __$CategoryCopyWithImpl<$Res>
    implements _$CategoryCopyWith<$Res> {
  __$CategoryCopyWithImpl(this._self, this._then);

  final _Category _self;
  final $Res Function(_Category) _then;

/// Create a copy of Category
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? id = null,Object? name = null,Object? description = freezed,Object? color = freezed,}) {
  return _then(_Category(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as int,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,color: freezed == color ? _self.color : color // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$Product {

 int get id; String get name; String get sku; String? get description;@JsonKey(fromJson: doubleFromJson) double get price; int get stockQuantity; int get minStock; int? get maxStock; int get reorderPoint; int get leadTimeDays; int? get categoryId; Category? get category; String? get imageUrl; String? get thumbnailUrl;
/// Create a copy of Product
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ProductCopyWith<Product> get copyWith => _$ProductCopyWithImpl<Product>(this as Product, _$identity);

  /// Serializes this Product to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is Product&&(identical(other.id, id) || other.id == id)&&(identical(other.name, name) || other.name == name)&&(identical(other.sku, sku) || other.sku == sku)&&(identical(other.description, description) || other.description == description)&&(identical(other.price, price) || other.price == price)&&(identical(other.stockQuantity, stockQuantity) || other.stockQuantity == stockQuantity)&&(identical(other.minStock, minStock) || other.minStock == minStock)&&(identical(other.maxStock, maxStock) || other.maxStock == maxStock)&&(identical(other.reorderPoint, reorderPoint) || other.reorderPoint == reorderPoint)&&(identical(other.leadTimeDays, leadTimeDays) || other.leadTimeDays == leadTimeDays)&&(identical(other.categoryId, categoryId) || other.categoryId == categoryId)&&(identical(other.category, category) || other.category == category)&&(identical(other.imageUrl, imageUrl) || other.imageUrl == imageUrl)&&(identical(other.thumbnailUrl, thumbnailUrl) || other.thumbnailUrl == thumbnailUrl));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,name,sku,description,price,stockQuantity,minStock,maxStock,reorderPoint,leadTimeDays,categoryId,category,imageUrl,thumbnailUrl);

@override
String toString() {
  return 'Product(id: $id, name: $name, sku: $sku, description: $description, price: $price, stockQuantity: $stockQuantity, minStock: $minStock, maxStock: $maxStock, reorderPoint: $reorderPoint, leadTimeDays: $leadTimeDays, categoryId: $categoryId, category: $category, imageUrl: $imageUrl, thumbnailUrl: $thumbnailUrl)';
}


}

/// @nodoc
abstract mixin class $ProductCopyWith<$Res>  {
  factory $ProductCopyWith(Product value, $Res Function(Product) _then) = _$ProductCopyWithImpl;
@useResult
$Res call({
 int id, String name, String sku, String? description,@JsonKey(fromJson: doubleFromJson) double price, int stockQuantity, int minStock, int? maxStock, int reorderPoint, int leadTimeDays, int? categoryId, Category? category, String? imageUrl, String? thumbnailUrl
});


$CategoryCopyWith<$Res>? get category;

}
/// @nodoc
class _$ProductCopyWithImpl<$Res>
    implements $ProductCopyWith<$Res> {
  _$ProductCopyWithImpl(this._self, this._then);

  final Product _self;
  final $Res Function(Product) _then;

/// Create a copy of Product
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? id = null,Object? name = null,Object? sku = null,Object? description = freezed,Object? price = null,Object? stockQuantity = null,Object? minStock = null,Object? maxStock = freezed,Object? reorderPoint = null,Object? leadTimeDays = null,Object? categoryId = freezed,Object? category = freezed,Object? imageUrl = freezed,Object? thumbnailUrl = freezed,}) {
  return _then(_self.copyWith(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as int,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,sku: null == sku ? _self.sku : sku // ignore: cast_nullable_to_non_nullable
as String,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,price: null == price ? _self.price : price // ignore: cast_nullable_to_non_nullable
as double,stockQuantity: null == stockQuantity ? _self.stockQuantity : stockQuantity // ignore: cast_nullable_to_non_nullable
as int,minStock: null == minStock ? _self.minStock : minStock // ignore: cast_nullable_to_non_nullable
as int,maxStock: freezed == maxStock ? _self.maxStock : maxStock // ignore: cast_nullable_to_non_nullable
as int?,reorderPoint: null == reorderPoint ? _self.reorderPoint : reorderPoint // ignore: cast_nullable_to_non_nullable
as int,leadTimeDays: null == leadTimeDays ? _self.leadTimeDays : leadTimeDays // ignore: cast_nullable_to_non_nullable
as int,categoryId: freezed == categoryId ? _self.categoryId : categoryId // ignore: cast_nullable_to_non_nullable
as int?,category: freezed == category ? _self.category : category // ignore: cast_nullable_to_non_nullable
as Category?,imageUrl: freezed == imageUrl ? _self.imageUrl : imageUrl // ignore: cast_nullable_to_non_nullable
as String?,thumbnailUrl: freezed == thumbnailUrl ? _self.thumbnailUrl : thumbnailUrl // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}
/// Create a copy of Product
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CategoryCopyWith<$Res>? get category {
    if (_self.category == null) {
    return null;
  }

  return $CategoryCopyWith<$Res>(_self.category!, (value) {
    return _then(_self.copyWith(category: value));
  });
}
}


/// Adds pattern-matching-related methods to [Product].
extension ProductPatterns on Product {
/// A variant of `map` that fallback to returning `orElse`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _Product value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _Product() when $default != null:
return $default(_that);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// Callbacks receives the raw object, upcasted.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case final Subclass2 value:
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _Product value)  $default,){
final _that = this;
switch (_that) {
case _Product():
return $default(_that);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `map` that fallback to returning `null`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _Product value)?  $default,){
final _that = this;
switch (_that) {
case _Product() when $default != null:
return $default(_that);case _:
  return null;

}
}
/// A variant of `when` that fallback to an `orElse` callback.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( int id,  String name,  String sku,  String? description, @JsonKey(fromJson: doubleFromJson)  double price,  int stockQuantity,  int minStock,  int? maxStock,  int reorderPoint,  int leadTimeDays,  int? categoryId,  Category? category,  String? imageUrl,  String? thumbnailUrl)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _Product() when $default != null:
return $default(_that.id,_that.name,_that.sku,_that.description,_that.price,_that.stockQuantity,_that.minStock,_that.maxStock,_that.reorderPoint,_that.leadTimeDays,_that.categoryId,_that.category,_that.imageUrl,_that.thumbnailUrl);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// As opposed to `map`, this offers destructuring.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case Subclass2(:final field2):
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( int id,  String name,  String sku,  String? description, @JsonKey(fromJson: doubleFromJson)  double price,  int stockQuantity,  int minStock,  int? maxStock,  int reorderPoint,  int leadTimeDays,  int? categoryId,  Category? category,  String? imageUrl,  String? thumbnailUrl)  $default,) {final _that = this;
switch (_that) {
case _Product():
return $default(_that.id,_that.name,_that.sku,_that.description,_that.price,_that.stockQuantity,_that.minStock,_that.maxStock,_that.reorderPoint,_that.leadTimeDays,_that.categoryId,_that.category,_that.imageUrl,_that.thumbnailUrl);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `when` that fallback to returning `null`
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( int id,  String name,  String sku,  String? description, @JsonKey(fromJson: doubleFromJson)  double price,  int stockQuantity,  int minStock,  int? maxStock,  int reorderPoint,  int leadTimeDays,  int? categoryId,  Category? category,  String? imageUrl,  String? thumbnailUrl)?  $default,) {final _that = this;
switch (_that) {
case _Product() when $default != null:
return $default(_that.id,_that.name,_that.sku,_that.description,_that.price,_that.stockQuantity,_that.minStock,_that.maxStock,_that.reorderPoint,_that.leadTimeDays,_that.categoryId,_that.category,_that.imageUrl,_that.thumbnailUrl);case _:
  return null;

}
}

}

/// @nodoc
@JsonSerializable()

class _Product extends Product {
  const _Product({required this.id, required this.name, required this.sku, this.description, @JsonKey(fromJson: doubleFromJson) required this.price, this.stockQuantity = 0, this.minStock = 0, this.maxStock, this.reorderPoint = 0, this.leadTimeDays = 0, this.categoryId, this.category, this.imageUrl, this.thumbnailUrl}): super._();
  factory _Product.fromJson(Map<String, dynamic> json) => _$ProductFromJson(json);

@override final  int id;
@override final  String name;
@override final  String sku;
@override final  String? description;
@override@JsonKey(fromJson: doubleFromJson) final  double price;
@override@JsonKey() final  int stockQuantity;
@override@JsonKey() final  int minStock;
@override final  int? maxStock;
@override@JsonKey() final  int reorderPoint;
@override@JsonKey() final  int leadTimeDays;
@override final  int? categoryId;
@override final  Category? category;
@override final  String? imageUrl;
@override final  String? thumbnailUrl;

/// Create a copy of Product
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ProductCopyWith<_Product> get copyWith => __$ProductCopyWithImpl<_Product>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ProductToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _Product&&(identical(other.id, id) || other.id == id)&&(identical(other.name, name) || other.name == name)&&(identical(other.sku, sku) || other.sku == sku)&&(identical(other.description, description) || other.description == description)&&(identical(other.price, price) || other.price == price)&&(identical(other.stockQuantity, stockQuantity) || other.stockQuantity == stockQuantity)&&(identical(other.minStock, minStock) || other.minStock == minStock)&&(identical(other.maxStock, maxStock) || other.maxStock == maxStock)&&(identical(other.reorderPoint, reorderPoint) || other.reorderPoint == reorderPoint)&&(identical(other.leadTimeDays, leadTimeDays) || other.leadTimeDays == leadTimeDays)&&(identical(other.categoryId, categoryId) || other.categoryId == categoryId)&&(identical(other.category, category) || other.category == category)&&(identical(other.imageUrl, imageUrl) || other.imageUrl == imageUrl)&&(identical(other.thumbnailUrl, thumbnailUrl) || other.thumbnailUrl == thumbnailUrl));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,id,name,sku,description,price,stockQuantity,minStock,maxStock,reorderPoint,leadTimeDays,categoryId,category,imageUrl,thumbnailUrl);

@override
String toString() {
  return 'Product(id: $id, name: $name, sku: $sku, description: $description, price: $price, stockQuantity: $stockQuantity, minStock: $minStock, maxStock: $maxStock, reorderPoint: $reorderPoint, leadTimeDays: $leadTimeDays, categoryId: $categoryId, category: $category, imageUrl: $imageUrl, thumbnailUrl: $thumbnailUrl)';
}


}

/// @nodoc
abstract mixin class _$ProductCopyWith<$Res> implements $ProductCopyWith<$Res> {
  factory _$ProductCopyWith(_Product value, $Res Function(_Product) _then) = __$ProductCopyWithImpl;
@override @useResult
$Res call({
 int id, String name, String sku, String? description,@JsonKey(fromJson: doubleFromJson) double price, int stockQuantity, int minStock, int? maxStock, int reorderPoint, int leadTimeDays, int? categoryId, Category? category, String? imageUrl, String? thumbnailUrl
});


@override $CategoryCopyWith<$Res>? get category;

}
/// @nodoc
class __$ProductCopyWithImpl<$Res>
    implements _$ProductCopyWith<$Res> {
  __$ProductCopyWithImpl(this._self, this._then);

  final _Product _self;
  final $Res Function(_Product) _then;

/// Create a copy of Product
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? id = null,Object? name = null,Object? sku = null,Object? description = freezed,Object? price = null,Object? stockQuantity = null,Object? minStock = null,Object? maxStock = freezed,Object? reorderPoint = null,Object? leadTimeDays = null,Object? categoryId = freezed,Object? category = freezed,Object? imageUrl = freezed,Object? thumbnailUrl = freezed,}) {
  return _then(_Product(
id: null == id ? _self.id : id // ignore: cast_nullable_to_non_nullable
as int,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,sku: null == sku ? _self.sku : sku // ignore: cast_nullable_to_non_nullable
as String,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,price: null == price ? _self.price : price // ignore: cast_nullable_to_non_nullable
as double,stockQuantity: null == stockQuantity ? _self.stockQuantity : stockQuantity // ignore: cast_nullable_to_non_nullable
as int,minStock: null == minStock ? _self.minStock : minStock // ignore: cast_nullable_to_non_nullable
as int,maxStock: freezed == maxStock ? _self.maxStock : maxStock // ignore: cast_nullable_to_non_nullable
as int?,reorderPoint: null == reorderPoint ? _self.reorderPoint : reorderPoint // ignore: cast_nullable_to_non_nullable
as int,leadTimeDays: null == leadTimeDays ? _self.leadTimeDays : leadTimeDays // ignore: cast_nullable_to_non_nullable
as int,categoryId: freezed == categoryId ? _self.categoryId : categoryId // ignore: cast_nullable_to_non_nullable
as int?,category: freezed == category ? _self.category : category // ignore: cast_nullable_to_non_nullable
as Category?,imageUrl: freezed == imageUrl ? _self.imageUrl : imageUrl // ignore: cast_nullable_to_non_nullable
as String?,thumbnailUrl: freezed == thumbnailUrl ? _self.thumbnailUrl : thumbnailUrl // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

/// Create a copy of Product
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$CategoryCopyWith<$Res>? get category {
    if (_self.category == null) {
    return null;
  }

  return $CategoryCopyWith<$Res>(_self.category!, (value) {
    return _then(_self.copyWith(category: value));
  });
}
}


/// @nodoc
mixin _$CatalogDelta {

 String get serverTime; List<Category> get categories; List<Product> get products; List<int> get deletedCategoryIds; List<int> get deletedProductIds;
/// Create a copy of CatalogDelta
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$CatalogDeltaCopyWith<CatalogDelta> get copyWith => _$CatalogDeltaCopyWithImpl<CatalogDelta>(this as CatalogDelta, _$identity);

  /// Serializes this CatalogDelta to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is CatalogDelta&&(identical(other.serverTime, serverTime) || other.serverTime == serverTime)&&const DeepCollectionEquality().equals(other.categories, categories)&&const DeepCollectionEquality().equals(other.products, products)&&const DeepCollectionEquality().equals(other.deletedCategoryIds, deletedCategoryIds)&&const DeepCollectionEquality().equals(other.deletedProductIds, deletedProductIds));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,serverTime,const DeepCollectionEquality().hash(categories),const DeepCollectionEquality().hash(products),const DeepCollectionEquality().hash(deletedCategoryIds),const DeepCollectionEquality().hash(deletedProductIds));

@override
String toString() {
  return 'CatalogDelta(serverTime: $serverTime, categories: $categories, products: $products, deletedCategoryIds: $deletedCategoryIds, deletedProductIds: $deletedProductIds)';
}


}

/// @nodoc
abstract mixin class $CatalogDeltaCopyWith<$Res>  {
  factory $CatalogDeltaCopyWith(CatalogDelta value, $Res Function(CatalogDelta) _then) = _$CatalogDeltaCopyWithImpl;
@useResult
$Res call({
 String serverTime, List<Category> categories, List<Product> products, List<int> deletedCategoryIds, List<int> deletedProductIds
});




}
/// @nodoc
class _$CatalogDeltaCopyWithImpl<$Res>
    implements $CatalogDeltaCopyWith<$Res> {
  _$CatalogDeltaCopyWithImpl(this._self, this._then);

  final CatalogDelta _self;
  final $Res Function(CatalogDelta) _then;

/// Create a copy of CatalogDelta
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? serverTime = null,Object? categories = null,Object? products = null,Object? deletedCategoryIds = null,Object? deletedProductIds = null,}) {
  return _then(_self.copyWith(
serverTime: null == serverTime ? _self.serverTime : serverTime // ignore: cast_nullable_to_non_nullable
as String,categories: null == categories ? _self.categories : categories // ignore: cast_nullable_to_non_nullable
as List<Category>,products: null == products ? _self.products : products // ignore: cast_nullable_to_non_nullable
as List<Product>,deletedCategoryIds: null == deletedCategoryIds ? _self.deletedCategoryIds : deletedCategoryIds // ignore: cast_nullable_to_non_nullable
as List<int>,deletedProductIds: null == deletedProductIds ? _self.deletedProductIds : deletedProductIds // ignore: cast_nullable_to_non_nullable
as List<int>,
  ));
}

}


/// Adds pattern-matching-related methods to [CatalogDelta].
extension CatalogDeltaPatterns on CatalogDelta {
/// A variant of `map` that fallback to returning `orElse`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _CatalogDelta value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _CatalogDelta() when $default != null:
return $default(_that);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// Callbacks receives the raw object, upcasted.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case final Subclass2 value:
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _CatalogDelta value)  $default,){
final _that = this;
switch (_that) {
case _CatalogDelta():
return $default(_that);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `map` that fallback to returning `null`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _CatalogDelta value)?  $default,){
final _that = this;
switch (_that) {
case _CatalogDelta() when $default != null:
return $default(_that);case _:
  return null;

}
}
/// A variant of `when` that fallback to an `orElse` callback.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( String serverTime,  List<Category> categories,  List<Product> products,  List<int> deletedCategoryIds,  List<int> deletedProductIds)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _CatalogDelta() when $default != null:
return $default(_that.serverTime,_that.categories,_that.products,_that.deletedCategoryIds,_that.deletedProductIds);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// As opposed to `map`, this offers destructuring.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case Subclass2(:final field2):
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( String serverTime,  List<Category> categories,  List<Product> products,  List<int> deletedCategoryIds,  List<int> deletedProductIds)  $default,) {final _that = this;
switch (_that) {
case _CatalogDelta():
return $default(_that.serverTime,_that.categories,_that.products,_that.deletedCategoryIds,_that.deletedProductIds);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `when` that fallback to returning `null`
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( String serverTime,  List<Category> categories,  List<Product> products,  List<int> deletedCategoryIds,  List<int> deletedProductIds)?  $default,) {final _that = this;
switch (_that) {
case _CatalogDelta() when $default != null:
return $default(_that.serverTime,_that.categories,_that.products,_that.deletedCategoryIds,_that.deletedProductIds);case _:
  return null;

}
}

}

/// @nodoc
@JsonSerializable()

class _CatalogDelta implements CatalogDelta {
  const _CatalogDelta({required this.serverTime, final  List<Category> categories = const [], final  List<Product> products = const [], final  List<int> deletedCategoryIds = const [], final  List<int> deletedProductIds = const []}): _categories = categories,_products = products,_deletedCategoryIds = deletedCategoryIds,_deletedProductIds = deletedProductIds;
  factory _CatalogDelta.fromJson(Map<String, dynamic> json) => _$CatalogDeltaFromJson(json);

@override final  String serverTime;
 final  List<Category> _categories;
@override@JsonKey() List<Category> get categories {
  if (_categories is EqualUnmodifiableListView) return _categories;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_categories);
}

 final  List<Product> _products;
@override@JsonKey() List<Product> get products {
  if (_products is EqualUnmodifiableListView) return _products;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_products);
}

 final  List<int> _deletedCategoryIds;
@override@JsonKey() List<int> get deletedCategoryIds {
  if (_deletedCategoryIds is EqualUnmodifiableListView) return _deletedCategoryIds;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_deletedCategoryIds);
}

 final  List<int> _deletedProductIds;
@override@JsonKey() List<int> get deletedProductIds {
  if (_deletedProductIds is EqualUnmodifiableListView) return _deletedProductIds;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_deletedProductIds);
}


/// Create a copy of CatalogDelta
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$CatalogDeltaCopyWith<_CatalogDelta> get copyWith => __$CatalogDeltaCopyWithImpl<_CatalogDelta>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$CatalogDeltaToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _CatalogDelta&&(identical(other.serverTime, serverTime) || other.serverTime == serverTime)&&const DeepCollectionEquality().equals(other._categories, _categories)&&const DeepCollectionEquality().equals(other._products, _products)&&const DeepCollectionEquality().equals(other._deletedCategoryIds, _deletedCategoryIds)&&const DeepCollectionEquality().equals(other._deletedProductIds, _deletedProductIds));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,serverTime,const DeepCollectionEquality().hash(_categories),const DeepCollectionEquality().hash(_products),const DeepCollectionEquality().hash(_deletedCategoryIds),const DeepCollectionEquality().hash(_deletedProductIds));

@override
String toString() {
  return 'CatalogDelta(serverTime: $serverTime, categories: $categories, products: $products, deletedCategoryIds: $deletedCategoryIds, deletedProductIds: $deletedProductIds)';
}


}

/// @nodoc
abstract mixin class _$CatalogDeltaCopyWith<$Res> implements $CatalogDeltaCopyWith<$Res> {
  factory _$CatalogDeltaCopyWith(_CatalogDelta value, $Res Function(_CatalogDelta) _then) = __$CatalogDeltaCopyWithImpl;
@override @useResult
$Res call({
 String serverTime, List<Category> categories, List<Product> products, List<int> deletedCategoryIds, List<int> deletedProductIds
});




}
/// @nodoc
class __$CatalogDeltaCopyWithImpl<$Res>
    implements _$CatalogDeltaCopyWith<$Res> {
  __$CatalogDeltaCopyWithImpl(this._self, this._then);

  final _CatalogDelta _self;
  final $Res Function(_CatalogDelta) _then;

/// Create a copy of CatalogDelta
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? serverTime = null,Object? categories = null,Object? products = null,Object? deletedCategoryIds = null,Object? deletedProductIds = null,}) {
  return _then(_CatalogDelta(
serverTime: null == serverTime ? _self.serverTime : serverTime // ignore: cast_nullable_to_non_nullable
as String,categories: null == categories ? _self._categories : categories // ignore: cast_nullable_to_non_nullable
as List<Category>,products: null == products ? _self._products : products // ignore: cast_nullable_to_non_nullable
as List<Product>,deletedCategoryIds: null == deletedCategoryIds ? _self._deletedCategoryIds : deletedCategoryIds // ignore: cast_nullable_to_non_nullable
as List<int>,deletedProductIds: null == deletedProductIds ? _self._deletedProductIds : deletedProductIds // ignore: cast_nullable_to_non_nullable
as List<int>,
  ));
}


}

// dart format on
