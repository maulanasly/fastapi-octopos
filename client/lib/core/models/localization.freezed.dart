// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'localization.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$LocalizationSetting {

 String get language; String get timezone; String get currency; String get dateFormat; String get numberFormat; String get countryCode;
/// Create a copy of LocalizationSetting
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$LocalizationSettingCopyWith<LocalizationSetting> get copyWith => _$LocalizationSettingCopyWithImpl<LocalizationSetting>(this as LocalizationSetting, _$identity);

  /// Serializes this LocalizationSetting to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is LocalizationSetting&&(identical(other.language, language) || other.language == language)&&(identical(other.timezone, timezone) || other.timezone == timezone)&&(identical(other.currency, currency) || other.currency == currency)&&(identical(other.dateFormat, dateFormat) || other.dateFormat == dateFormat)&&(identical(other.numberFormat, numberFormat) || other.numberFormat == numberFormat)&&(identical(other.countryCode, countryCode) || other.countryCode == countryCode));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,language,timezone,currency,dateFormat,numberFormat,countryCode);

@override
String toString() {
  return 'LocalizationSetting(language: $language, timezone: $timezone, currency: $currency, dateFormat: $dateFormat, numberFormat: $numberFormat, countryCode: $countryCode)';
}


}

/// @nodoc
abstract mixin class $LocalizationSettingCopyWith<$Res>  {
  factory $LocalizationSettingCopyWith(LocalizationSetting value, $Res Function(LocalizationSetting) _then) = _$LocalizationSettingCopyWithImpl;
@useResult
$Res call({
 String language, String timezone, String currency, String dateFormat, String numberFormat, String countryCode
});




}
/// @nodoc
class _$LocalizationSettingCopyWithImpl<$Res>
    implements $LocalizationSettingCopyWith<$Res> {
  _$LocalizationSettingCopyWithImpl(this._self, this._then);

  final LocalizationSetting _self;
  final $Res Function(LocalizationSetting) _then;

/// Create a copy of LocalizationSetting
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? language = null,Object? timezone = null,Object? currency = null,Object? dateFormat = null,Object? numberFormat = null,Object? countryCode = null,}) {
  return _then(_self.copyWith(
language: null == language ? _self.language : language // ignore: cast_nullable_to_non_nullable
as String,timezone: null == timezone ? _self.timezone : timezone // ignore: cast_nullable_to_non_nullable
as String,currency: null == currency ? _self.currency : currency // ignore: cast_nullable_to_non_nullable
as String,dateFormat: null == dateFormat ? _self.dateFormat : dateFormat // ignore: cast_nullable_to_non_nullable
as String,numberFormat: null == numberFormat ? _self.numberFormat : numberFormat // ignore: cast_nullable_to_non_nullable
as String,countryCode: null == countryCode ? _self.countryCode : countryCode // ignore: cast_nullable_to_non_nullable
as String,
  ));
}

}


/// Adds pattern-matching-related methods to [LocalizationSetting].
extension LocalizationSettingPatterns on LocalizationSetting {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _LocalizationSetting value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _LocalizationSetting() when $default != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _LocalizationSetting value)  $default,){
final _that = this;
switch (_that) {
case _LocalizationSetting():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _LocalizationSetting value)?  $default,){
final _that = this;
switch (_that) {
case _LocalizationSetting() when $default != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( String language,  String timezone,  String currency,  String dateFormat,  String numberFormat,  String countryCode)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _LocalizationSetting() when $default != null:
return $default(_that.language,_that.timezone,_that.currency,_that.dateFormat,_that.numberFormat,_that.countryCode);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( String language,  String timezone,  String currency,  String dateFormat,  String numberFormat,  String countryCode)  $default,) {final _that = this;
switch (_that) {
case _LocalizationSetting():
return $default(_that.language,_that.timezone,_that.currency,_that.dateFormat,_that.numberFormat,_that.countryCode);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( String language,  String timezone,  String currency,  String dateFormat,  String numberFormat,  String countryCode)?  $default,) {final _that = this;
switch (_that) {
case _LocalizationSetting() when $default != null:
return $default(_that.language,_that.timezone,_that.currency,_that.dateFormat,_that.numberFormat,_that.countryCode);case _:
  return null;

}
}

}

/// @nodoc
@JsonSerializable()

class _LocalizationSetting implements LocalizationSetting {
  const _LocalizationSetting({required this.language, required this.timezone, required this.currency, required this.dateFormat, required this.numberFormat, required this.countryCode});
  factory _LocalizationSetting.fromJson(Map<String, dynamic> json) => _$LocalizationSettingFromJson(json);

@override final  String language;
@override final  String timezone;
@override final  String currency;
@override final  String dateFormat;
@override final  String numberFormat;
@override final  String countryCode;

/// Create a copy of LocalizationSetting
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$LocalizationSettingCopyWith<_LocalizationSetting> get copyWith => __$LocalizationSettingCopyWithImpl<_LocalizationSetting>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$LocalizationSettingToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _LocalizationSetting&&(identical(other.language, language) || other.language == language)&&(identical(other.timezone, timezone) || other.timezone == timezone)&&(identical(other.currency, currency) || other.currency == currency)&&(identical(other.dateFormat, dateFormat) || other.dateFormat == dateFormat)&&(identical(other.numberFormat, numberFormat) || other.numberFormat == numberFormat)&&(identical(other.countryCode, countryCode) || other.countryCode == countryCode));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,language,timezone,currency,dateFormat,numberFormat,countryCode);

@override
String toString() {
  return 'LocalizationSetting(language: $language, timezone: $timezone, currency: $currency, dateFormat: $dateFormat, numberFormat: $numberFormat, countryCode: $countryCode)';
}


}

/// @nodoc
abstract mixin class _$LocalizationSettingCopyWith<$Res> implements $LocalizationSettingCopyWith<$Res> {
  factory _$LocalizationSettingCopyWith(_LocalizationSetting value, $Res Function(_LocalizationSetting) _then) = __$LocalizationSettingCopyWithImpl;
@override @useResult
$Res call({
 String language, String timezone, String currency, String dateFormat, String numberFormat, String countryCode
});




}
/// @nodoc
class __$LocalizationSettingCopyWithImpl<$Res>
    implements _$LocalizationSettingCopyWith<$Res> {
  __$LocalizationSettingCopyWithImpl(this._self, this._then);

  final _LocalizationSetting _self;
  final $Res Function(_LocalizationSetting) _then;

/// Create a copy of LocalizationSetting
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? language = null,Object? timezone = null,Object? currency = null,Object? dateFormat = null,Object? numberFormat = null,Object? countryCode = null,}) {
  return _then(_LocalizationSetting(
language: null == language ? _self.language : language // ignore: cast_nullable_to_non_nullable
as String,timezone: null == timezone ? _self.timezone : timezone // ignore: cast_nullable_to_non_nullable
as String,currency: null == currency ? _self.currency : currency // ignore: cast_nullable_to_non_nullable
as String,dateFormat: null == dateFormat ? _self.dateFormat : dateFormat // ignore: cast_nullable_to_non_nullable
as String,numberFormat: null == numberFormat ? _self.numberFormat : numberFormat // ignore: cast_nullable_to_non_nullable
as String,countryCode: null == countryCode ? _self.countryCode : countryCode // ignore: cast_nullable_to_non_nullable
as String,
  ));
}


}


/// @nodoc
mixin _$LocalizationRegion {

 String get countryCode; String get language; String get timezone; String get currency; String get dateFormat; String get numberFormat;
/// Create a copy of LocalizationRegion
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$LocalizationRegionCopyWith<LocalizationRegion> get copyWith => _$LocalizationRegionCopyWithImpl<LocalizationRegion>(this as LocalizationRegion, _$identity);

  /// Serializes this LocalizationRegion to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is LocalizationRegion&&(identical(other.countryCode, countryCode) || other.countryCode == countryCode)&&(identical(other.language, language) || other.language == language)&&(identical(other.timezone, timezone) || other.timezone == timezone)&&(identical(other.currency, currency) || other.currency == currency)&&(identical(other.dateFormat, dateFormat) || other.dateFormat == dateFormat)&&(identical(other.numberFormat, numberFormat) || other.numberFormat == numberFormat));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,countryCode,language,timezone,currency,dateFormat,numberFormat);

@override
String toString() {
  return 'LocalizationRegion(countryCode: $countryCode, language: $language, timezone: $timezone, currency: $currency, dateFormat: $dateFormat, numberFormat: $numberFormat)';
}


}

/// @nodoc
abstract mixin class $LocalizationRegionCopyWith<$Res>  {
  factory $LocalizationRegionCopyWith(LocalizationRegion value, $Res Function(LocalizationRegion) _then) = _$LocalizationRegionCopyWithImpl;
@useResult
$Res call({
 String countryCode, String language, String timezone, String currency, String dateFormat, String numberFormat
});




}
/// @nodoc
class _$LocalizationRegionCopyWithImpl<$Res>
    implements $LocalizationRegionCopyWith<$Res> {
  _$LocalizationRegionCopyWithImpl(this._self, this._then);

  final LocalizationRegion _self;
  final $Res Function(LocalizationRegion) _then;

/// Create a copy of LocalizationRegion
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? countryCode = null,Object? language = null,Object? timezone = null,Object? currency = null,Object? dateFormat = null,Object? numberFormat = null,}) {
  return _then(_self.copyWith(
countryCode: null == countryCode ? _self.countryCode : countryCode // ignore: cast_nullable_to_non_nullable
as String,language: null == language ? _self.language : language // ignore: cast_nullable_to_non_nullable
as String,timezone: null == timezone ? _self.timezone : timezone // ignore: cast_nullable_to_non_nullable
as String,currency: null == currency ? _self.currency : currency // ignore: cast_nullable_to_non_nullable
as String,dateFormat: null == dateFormat ? _self.dateFormat : dateFormat // ignore: cast_nullable_to_non_nullable
as String,numberFormat: null == numberFormat ? _self.numberFormat : numberFormat // ignore: cast_nullable_to_non_nullable
as String,
  ));
}

}


/// Adds pattern-matching-related methods to [LocalizationRegion].
extension LocalizationRegionPatterns on LocalizationRegion {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _LocalizationRegion value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _LocalizationRegion() when $default != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _LocalizationRegion value)  $default,){
final _that = this;
switch (_that) {
case _LocalizationRegion():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _LocalizationRegion value)?  $default,){
final _that = this;
switch (_that) {
case _LocalizationRegion() when $default != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( String countryCode,  String language,  String timezone,  String currency,  String dateFormat,  String numberFormat)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _LocalizationRegion() when $default != null:
return $default(_that.countryCode,_that.language,_that.timezone,_that.currency,_that.dateFormat,_that.numberFormat);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( String countryCode,  String language,  String timezone,  String currency,  String dateFormat,  String numberFormat)  $default,) {final _that = this;
switch (_that) {
case _LocalizationRegion():
return $default(_that.countryCode,_that.language,_that.timezone,_that.currency,_that.dateFormat,_that.numberFormat);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( String countryCode,  String language,  String timezone,  String currency,  String dateFormat,  String numberFormat)?  $default,) {final _that = this;
switch (_that) {
case _LocalizationRegion() when $default != null:
return $default(_that.countryCode,_that.language,_that.timezone,_that.currency,_that.dateFormat,_that.numberFormat);case _:
  return null;

}
}

}

/// @nodoc
@JsonSerializable()

class _LocalizationRegion implements LocalizationRegion {
  const _LocalizationRegion({required this.countryCode, required this.language, required this.timezone, required this.currency, required this.dateFormat, required this.numberFormat});
  factory _LocalizationRegion.fromJson(Map<String, dynamic> json) => _$LocalizationRegionFromJson(json);

@override final  String countryCode;
@override final  String language;
@override final  String timezone;
@override final  String currency;
@override final  String dateFormat;
@override final  String numberFormat;

/// Create a copy of LocalizationRegion
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$LocalizationRegionCopyWith<_LocalizationRegion> get copyWith => __$LocalizationRegionCopyWithImpl<_LocalizationRegion>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$LocalizationRegionToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _LocalizationRegion&&(identical(other.countryCode, countryCode) || other.countryCode == countryCode)&&(identical(other.language, language) || other.language == language)&&(identical(other.timezone, timezone) || other.timezone == timezone)&&(identical(other.currency, currency) || other.currency == currency)&&(identical(other.dateFormat, dateFormat) || other.dateFormat == dateFormat)&&(identical(other.numberFormat, numberFormat) || other.numberFormat == numberFormat));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,countryCode,language,timezone,currency,dateFormat,numberFormat);

@override
String toString() {
  return 'LocalizationRegion(countryCode: $countryCode, language: $language, timezone: $timezone, currency: $currency, dateFormat: $dateFormat, numberFormat: $numberFormat)';
}


}

/// @nodoc
abstract mixin class _$LocalizationRegionCopyWith<$Res> implements $LocalizationRegionCopyWith<$Res> {
  factory _$LocalizationRegionCopyWith(_LocalizationRegion value, $Res Function(_LocalizationRegion) _then) = __$LocalizationRegionCopyWithImpl;
@override @useResult
$Res call({
 String countryCode, String language, String timezone, String currency, String dateFormat, String numberFormat
});




}
/// @nodoc
class __$LocalizationRegionCopyWithImpl<$Res>
    implements _$LocalizationRegionCopyWith<$Res> {
  __$LocalizationRegionCopyWithImpl(this._self, this._then);

  final _LocalizationRegion _self;
  final $Res Function(_LocalizationRegion) _then;

/// Create a copy of LocalizationRegion
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? countryCode = null,Object? language = null,Object? timezone = null,Object? currency = null,Object? dateFormat = null,Object? numberFormat = null,}) {
  return _then(_LocalizationRegion(
countryCode: null == countryCode ? _self.countryCode : countryCode // ignore: cast_nullable_to_non_nullable
as String,language: null == language ? _self.language : language // ignore: cast_nullable_to_non_nullable
as String,timezone: null == timezone ? _self.timezone : timezone // ignore: cast_nullable_to_non_nullable
as String,currency: null == currency ? _self.currency : currency // ignore: cast_nullable_to_non_nullable
as String,dateFormat: null == dateFormat ? _self.dateFormat : dateFormat // ignore: cast_nullable_to_non_nullable
as String,numberFormat: null == numberFormat ? _self.numberFormat : numberFormat // ignore: cast_nullable_to_non_nullable
as String,
  ));
}


}


/// @nodoc
mixin _$LocalizationOptions {

 List<String> get languages; List<String> get currencies; List<String> get timezones; List<String> get dateFormats; List<String> get numberFormats; List<String> get countryCodes;
/// Create a copy of LocalizationOptions
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$LocalizationOptionsCopyWith<LocalizationOptions> get copyWith => _$LocalizationOptionsCopyWithImpl<LocalizationOptions>(this as LocalizationOptions, _$identity);

  /// Serializes this LocalizationOptions to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is LocalizationOptions&&const DeepCollectionEquality().equals(other.languages, languages)&&const DeepCollectionEquality().equals(other.currencies, currencies)&&const DeepCollectionEquality().equals(other.timezones, timezones)&&const DeepCollectionEquality().equals(other.dateFormats, dateFormats)&&const DeepCollectionEquality().equals(other.numberFormats, numberFormats)&&const DeepCollectionEquality().equals(other.countryCodes, countryCodes));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,const DeepCollectionEquality().hash(languages),const DeepCollectionEquality().hash(currencies),const DeepCollectionEquality().hash(timezones),const DeepCollectionEquality().hash(dateFormats),const DeepCollectionEquality().hash(numberFormats),const DeepCollectionEquality().hash(countryCodes));

@override
String toString() {
  return 'LocalizationOptions(languages: $languages, currencies: $currencies, timezones: $timezones, dateFormats: $dateFormats, numberFormats: $numberFormats, countryCodes: $countryCodes)';
}


}

/// @nodoc
abstract mixin class $LocalizationOptionsCopyWith<$Res>  {
  factory $LocalizationOptionsCopyWith(LocalizationOptions value, $Res Function(LocalizationOptions) _then) = _$LocalizationOptionsCopyWithImpl;
@useResult
$Res call({
 List<String> languages, List<String> currencies, List<String> timezones, List<String> dateFormats, List<String> numberFormats, List<String> countryCodes
});




}
/// @nodoc
class _$LocalizationOptionsCopyWithImpl<$Res>
    implements $LocalizationOptionsCopyWith<$Res> {
  _$LocalizationOptionsCopyWithImpl(this._self, this._then);

  final LocalizationOptions _self;
  final $Res Function(LocalizationOptions) _then;

/// Create a copy of LocalizationOptions
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? languages = null,Object? currencies = null,Object? timezones = null,Object? dateFormats = null,Object? numberFormats = null,Object? countryCodes = null,}) {
  return _then(_self.copyWith(
languages: null == languages ? _self.languages : languages // ignore: cast_nullable_to_non_nullable
as List<String>,currencies: null == currencies ? _self.currencies : currencies // ignore: cast_nullable_to_non_nullable
as List<String>,timezones: null == timezones ? _self.timezones : timezones // ignore: cast_nullable_to_non_nullable
as List<String>,dateFormats: null == dateFormats ? _self.dateFormats : dateFormats // ignore: cast_nullable_to_non_nullable
as List<String>,numberFormats: null == numberFormats ? _self.numberFormats : numberFormats // ignore: cast_nullable_to_non_nullable
as List<String>,countryCodes: null == countryCodes ? _self.countryCodes : countryCodes // ignore: cast_nullable_to_non_nullable
as List<String>,
  ));
}

}


/// Adds pattern-matching-related methods to [LocalizationOptions].
extension LocalizationOptionsPatterns on LocalizationOptions {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _LocalizationOptions value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _LocalizationOptions() when $default != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _LocalizationOptions value)  $default,){
final _that = this;
switch (_that) {
case _LocalizationOptions():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _LocalizationOptions value)?  $default,){
final _that = this;
switch (_that) {
case _LocalizationOptions() when $default != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( List<String> languages,  List<String> currencies,  List<String> timezones,  List<String> dateFormats,  List<String> numberFormats,  List<String> countryCodes)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _LocalizationOptions() when $default != null:
return $default(_that.languages,_that.currencies,_that.timezones,_that.dateFormats,_that.numberFormats,_that.countryCodes);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( List<String> languages,  List<String> currencies,  List<String> timezones,  List<String> dateFormats,  List<String> numberFormats,  List<String> countryCodes)  $default,) {final _that = this;
switch (_that) {
case _LocalizationOptions():
return $default(_that.languages,_that.currencies,_that.timezones,_that.dateFormats,_that.numberFormats,_that.countryCodes);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( List<String> languages,  List<String> currencies,  List<String> timezones,  List<String> dateFormats,  List<String> numberFormats,  List<String> countryCodes)?  $default,) {final _that = this;
switch (_that) {
case _LocalizationOptions() when $default != null:
return $default(_that.languages,_that.currencies,_that.timezones,_that.dateFormats,_that.numberFormats,_that.countryCodes);case _:
  return null;

}
}

}

/// @nodoc
@JsonSerializable()

class _LocalizationOptions implements LocalizationOptions {
  const _LocalizationOptions({required List<String> languages, required List<String> currencies, required List<String> timezones, required List<String> dateFormats, required List<String> numberFormats, required List<String> countryCodes}): _languages = languages,_currencies = currencies,_timezones = timezones,_dateFormats = dateFormats,_numberFormats = numberFormats,_countryCodes = countryCodes;
  factory _LocalizationOptions.fromJson(Map<String, dynamic> json) => _$LocalizationOptionsFromJson(json);

 final  List<String> _languages;
@override List<String> get languages {
  if (_languages is EqualUnmodifiableListView) return _languages;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_languages);
}

 final  List<String> _currencies;
@override List<String> get currencies {
  if (_currencies is EqualUnmodifiableListView) return _currencies;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_currencies);
}

 final  List<String> _timezones;
@override List<String> get timezones {
  if (_timezones is EqualUnmodifiableListView) return _timezones;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_timezones);
}

 final  List<String> _dateFormats;
@override List<String> get dateFormats {
  if (_dateFormats is EqualUnmodifiableListView) return _dateFormats;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_dateFormats);
}

 final  List<String> _numberFormats;
@override List<String> get numberFormats {
  if (_numberFormats is EqualUnmodifiableListView) return _numberFormats;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_numberFormats);
}

 final  List<String> _countryCodes;
@override List<String> get countryCodes {
  if (_countryCodes is EqualUnmodifiableListView) return _countryCodes;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_countryCodes);
}


/// Create a copy of LocalizationOptions
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$LocalizationOptionsCopyWith<_LocalizationOptions> get copyWith => __$LocalizationOptionsCopyWithImpl<_LocalizationOptions>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$LocalizationOptionsToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _LocalizationOptions&&const DeepCollectionEquality().equals(other._languages, _languages)&&const DeepCollectionEquality().equals(other._currencies, _currencies)&&const DeepCollectionEquality().equals(other._timezones, _timezones)&&const DeepCollectionEquality().equals(other._dateFormats, _dateFormats)&&const DeepCollectionEquality().equals(other._numberFormats, _numberFormats)&&const DeepCollectionEquality().equals(other._countryCodes, _countryCodes));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,const DeepCollectionEquality().hash(_languages),const DeepCollectionEquality().hash(_currencies),const DeepCollectionEquality().hash(_timezones),const DeepCollectionEquality().hash(_dateFormats),const DeepCollectionEquality().hash(_numberFormats),const DeepCollectionEquality().hash(_countryCodes));

@override
String toString() {
  return 'LocalizationOptions(languages: $languages, currencies: $currencies, timezones: $timezones, dateFormats: $dateFormats, numberFormats: $numberFormats, countryCodes: $countryCodes)';
}


}

/// @nodoc
abstract mixin class _$LocalizationOptionsCopyWith<$Res> implements $LocalizationOptionsCopyWith<$Res> {
  factory _$LocalizationOptionsCopyWith(_LocalizationOptions value, $Res Function(_LocalizationOptions) _then) = __$LocalizationOptionsCopyWithImpl;
@override @useResult
$Res call({
 List<String> languages, List<String> currencies, List<String> timezones, List<String> dateFormats, List<String> numberFormats, List<String> countryCodes
});




}
/// @nodoc
class __$LocalizationOptionsCopyWithImpl<$Res>
    implements _$LocalizationOptionsCopyWith<$Res> {
  __$LocalizationOptionsCopyWithImpl(this._self, this._then);

  final _LocalizationOptions _self;
  final $Res Function(_LocalizationOptions) _then;

/// Create a copy of LocalizationOptions
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? languages = null,Object? currencies = null,Object? timezones = null,Object? dateFormats = null,Object? numberFormats = null,Object? countryCodes = null,}) {
  return _then(_LocalizationOptions(
languages: null == languages ? _self._languages : languages // ignore: cast_nullable_to_non_nullable
as List<String>,currencies: null == currencies ? _self._currencies : currencies // ignore: cast_nullable_to_non_nullable
as List<String>,timezones: null == timezones ? _self._timezones : timezones // ignore: cast_nullable_to_non_nullable
as List<String>,dateFormats: null == dateFormats ? _self._dateFormats : dateFormats // ignore: cast_nullable_to_non_nullable
as List<String>,numberFormats: null == numberFormats ? _self._numberFormats : numberFormats // ignore: cast_nullable_to_non_nullable
as List<String>,countryCodes: null == countryCodes ? _self._countryCodes : countryCodes // ignore: cast_nullable_to_non_nullable
as List<String>,
  ));
}


}

// dart format on
