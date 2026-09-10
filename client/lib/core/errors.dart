/// Friendly, localized error mapping for API failures.
///
/// DioExceptions carry raw text (URLs, stack-ish detail) that should never
/// reach the user. Map by status code first, then by message hints, and
/// always fall back to a generic connection message.
library;

import 'package:dio/dio.dart';
import 'package:geolocator/geolocator.dart';

import 'strings.dart';

/// Maps a thrown [error] to a friendly localized message.
String friendlyError(Object error, AppStrings strings) {
  if (error is DioException) {
    final status = error.response?.statusCode;
    final detail = _detailFrom(error);
    switch (status) {
      case 400:
        if (detail != null && detail.toLowerCase().contains('locked')) {
          return strings.of('accountLocked');
        }
        return strings.of('badCredentials');
      case 401:
        return strings.of('sessionExpired');
      case 403:
        return strings.of('forbidden');
      case 404:
        return strings.of('notFound');
      case 409:
        return strings.of('conflict');
      case 413:
        return strings.of('imageTooLarge');
      case 415:
        return strings.of('unsupportedImage');
      case 422:
        final fieldDetail = _fieldErrorsFrom(error);
        if (fieldDetail != null) return fieldDetail;
        return strings.of('validationFailed');
      case 423:
        return strings.of('accountLocked');
      case 429:
        return strings.of('rateLimited');
    }
    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.connectionError ||
        error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.sendTimeout) {
      return strings.of('cannotReachServer');
    }
    return strings.of('genericError');
  }
  return strings.of('genericError');
}

/// Maps a geolocation failure to a message that tells the user how to
/// fix it: denied permission and disabled services need different
/// action than a transient outage.
String locationErrorMessage(Object error, AppStrings strings) {
  if (error is PermissionDeniedException) {
    return strings.of('locationPermissionDenied');
  }
  if (error is LocationServiceDisabledException) {
    return strings.of('locationServiceDisabled');
  }
  return strings.of('locationUnavailable');
}

/// Maps an outbox row's stored error to a localized message. The sync
/// service stores stable codes (`http_<code>`, `unexpected_error`);
/// anything else is a legacy raw string shown as-is.
String outboxRowErrorMessage(String? stored, AppStrings strings) {
  if (stored == null || stored.isEmpty) return strings.of('genericError');
  final http = RegExp(r'^http_(\d+)$').firstMatch(stored);
  if (http != null) {
    return switch (int.tryParse(http.group(1)!)) {
      400 => strings.of('validationFailed'),
      401 => strings.of('sessionExpired'),
      403 => strings.of('forbidden'),
      404 => strings.of('notFound'),
      409 => strings.of('conflict'),
      422 => strings.of('validationFailed'),
      _ => strings.of('genericError'),
    };
  }
  if (stored == 'unexpected_error') return strings.of('genericError');
  return stored;
}

String? _detailFrom(DioException error) {
  final data = error.response?.data;
  if (data is Map && data['detail'] is String) {
    return data['detail'] as String;
  }
  return null;
}

/// Renders FastAPI's structured 422 body
/// (`detail: [{loc, msg, type}, ...]`) as a readable, per-field string.
String? _fieldErrorsFrom(DioException error) {
  final data = error.response?.data;
  if (data is! Map) return null;
  final detail = data['detail'];
  if (detail is! List || detail.isEmpty) return null;
  final lines = <String>[];
  for (final item in detail) {
    if (item is! Map) continue;
    final loc = item['loc'];
    final field = loc is List && loc.isNotEmpty
        ? loc[loc.length - 1].toString()
        : null;
    final msg = item['msg'];
    if (msg is! String || msg.isEmpty) continue;
    lines.add(field != null ? '$field: $msg' : msg);
  }
  if (lines.isEmpty) return null;
  return lines.take(3).join('\n');
}
