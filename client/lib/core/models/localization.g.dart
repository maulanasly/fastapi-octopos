// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'localization.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_LocalizationSetting _$LocalizationSettingFromJson(Map<String, dynamic> json) =>
    $checkedCreate(
      '_LocalizationSetting',
      json,
      ($checkedConvert) {
        final val = _LocalizationSetting(
          language: $checkedConvert('language', (v) => v as String),
          timezone: $checkedConvert('timezone', (v) => v as String),
          currency: $checkedConvert('currency', (v) => v as String),
          dateFormat: $checkedConvert('date_format', (v) => v as String),
          numberFormat: $checkedConvert('number_format', (v) => v as String),
          countryCode: $checkedConvert('country_code', (v) => v as String),
        );
        return val;
      },
      fieldKeyMap: const {
        'dateFormat': 'date_format',
        'numberFormat': 'number_format',
        'countryCode': 'country_code',
      },
    );

Map<String, dynamic> _$LocalizationSettingToJson(
  _LocalizationSetting instance,
) => <String, dynamic>{
  'language': instance.language,
  'timezone': instance.timezone,
  'currency': instance.currency,
  'date_format': instance.dateFormat,
  'number_format': instance.numberFormat,
  'country_code': instance.countryCode,
};

_LocalizationRegion _$LocalizationRegionFromJson(Map<String, dynamic> json) =>
    $checkedCreate(
      '_LocalizationRegion',
      json,
      ($checkedConvert) {
        final val = _LocalizationRegion(
          countryCode: $checkedConvert('country_code', (v) => v as String),
          language: $checkedConvert('language', (v) => v as String),
          timezone: $checkedConvert('timezone', (v) => v as String),
          currency: $checkedConvert('currency', (v) => v as String),
          dateFormat: $checkedConvert('date_format', (v) => v as String),
          numberFormat: $checkedConvert('number_format', (v) => v as String),
        );
        return val;
      },
      fieldKeyMap: const {
        'countryCode': 'country_code',
        'dateFormat': 'date_format',
        'numberFormat': 'number_format',
      },
    );

Map<String, dynamic> _$LocalizationRegionToJson(_LocalizationRegion instance) =>
    <String, dynamic>{
      'country_code': instance.countryCode,
      'language': instance.language,
      'timezone': instance.timezone,
      'currency': instance.currency,
      'date_format': instance.dateFormat,
      'number_format': instance.numberFormat,
    };

_LocalizationOptions _$LocalizationOptionsFromJson(Map<String, dynamic> json) =>
    $checkedCreate(
      '_LocalizationOptions',
      json,
      ($checkedConvert) {
        final val = _LocalizationOptions(
          languages: $checkedConvert(
            'languages',
            (v) => (v as List<dynamic>).map((e) => e as String).toList(),
          ),
          currencies: $checkedConvert(
            'currencies',
            (v) => (v as List<dynamic>).map((e) => e as String).toList(),
          ),
          timezones: $checkedConvert(
            'timezones',
            (v) => (v as List<dynamic>).map((e) => e as String).toList(),
          ),
          dateFormats: $checkedConvert(
            'date_formats',
            (v) => (v as List<dynamic>).map((e) => e as String).toList(),
          ),
          numberFormats: $checkedConvert(
            'number_formats',
            (v) => (v as List<dynamic>).map((e) => e as String).toList(),
          ),
          countryCodes: $checkedConvert(
            'country_codes',
            (v) => (v as List<dynamic>).map((e) => e as String).toList(),
          ),
        );
        return val;
      },
      fieldKeyMap: const {
        'dateFormats': 'date_formats',
        'numberFormats': 'number_formats',
        'countryCodes': 'country_codes',
      },
    );

Map<String, dynamic> _$LocalizationOptionsToJson(
  _LocalizationOptions instance,
) => <String, dynamic>{
  'languages': instance.languages,
  'currencies': instance.currencies,
  'timezones': instance.timezones,
  'date_formats': instance.dateFormats,
  'number_formats': instance.numberFormats,
  'country_codes': instance.countryCodes,
};
