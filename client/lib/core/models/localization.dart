import 'package:freezed_annotation/freezed_annotation.dart';

part 'localization.freezed.dart';
part 'localization.g.dart';

@freezed
abstract class LocalizationSetting with _$LocalizationSetting {
  const factory LocalizationSetting({
    required String language,
    required String timezone,
    required String currency,
    required String dateFormat,
    required String numberFormat,
    required String countryCode,
  }) = _LocalizationSetting;

  factory LocalizationSetting.fromJson(Map<String, dynamic> json) =>
      _$LocalizationSettingFromJson(json);
}

@freezed
abstract class LocalizationRegion with _$LocalizationRegion {
  const factory LocalizationRegion({
    required String countryCode,
    required String language,
    required String timezone,
    required String currency,
    required String dateFormat,
    required String numberFormat,
  }) = _LocalizationRegion;

  factory LocalizationRegion.fromJson(Map<String, dynamic> json) =>
      _$LocalizationRegionFromJson(json);
}

@freezed
abstract class LocalizationOptions with _$LocalizationOptions {
  const factory LocalizationOptions({
    required List<String> languages,
    required List<String> currencies,
    required List<String> timezones,
    required List<String> dateFormats,
    required List<String> numberFormats,
    required List<String> countryCodes,
  }) = _LocalizationOptions;

  factory LocalizationOptions.fromJson(Map<String, dynamic> json) =>
      _$LocalizationOptionsFromJson(json);
}
