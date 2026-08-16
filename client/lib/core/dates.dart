/// Region-aware date formatting.
///
/// The backend serializes datetimes as ISO-8601 UTC; display converts to
/// the region timezone (from the localization setting) using the `timezone`
/// package and the setting's date_format (strftime-style), mapped to intl
/// patterns for the shipped presets.
library;

import 'package:intl/intl.dart';
import 'package:timezone/data/latest_all.dart' as tzdata;
import 'package:timezone/timezone.dart' as tz;

bool _tzInitialized = false;

void _ensureTz() {
  if (_tzInitialized) return;
  tzdata.initializeTimeZones();
  _tzInitialized = true;
}

String _activeTz = 'UTC';
String _activeFormat = 'yyyy-MM-dd HH:mm:ss';

/// Maps a strftime-style format (from the backend setting) to an intl
/// DateFormat pattern. Unsupported tokens fall back to the shipped default.
String _toIntlPattern(String strftimeFormat) {
  switch (strftimeFormat) {
    case '%Y-%m-%d %H:%M:%S':
      return 'yyyy-MM-dd HH:mm:ss';
    case '%d-%m-%Y %H:%M':
      return 'dd-MM-yyyy HH:mm';
    case '%Y-%m-%d':
      return 'yyyy-MM-dd';
    default:
      return 'yyyy-MM-dd HH:mm:ss';
  }
}

/// Sets the active display timezone and date format (strftime-style).
void configureDates({required String timezone, required String dateFormat}) {
  _ensureTz();
  _activeTz = timezone;
  _activeFormat = _toIntlPattern(dateFormat);
}

/// Formats an ISO-8601 UTC datetime string in the active region timezone.
String formatDateTimeIso(String? iso, {String? overrideFormat}) {
  if (iso == null || iso.isEmpty) return '-';
  final parsed = DateTime.tryParse(iso);
  if (parsed == null) return iso;
  return formatDateTime(parsed, overrideFormat: overrideFormat);
}

/// Formats a [DateTime] (naive or UTC) in the active region timezone.
String formatDateTime(DateTime dt, {String? overrideFormat}) {
  _ensureTz();
  final utc = dt.isUtc ? dt : dt.toUtc();
  tz.Location location;
  try {
    location = tz.getLocation(_activeTz);
  } catch (_) {
    location = tz.getLocation('UTC');
  }
  final zoned = tz.TZDateTime.from(utc, location);
  return DateFormat(overrideFormat ?? _activeFormat).format(zoned);
}
