import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/errors.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/core/strings.dart';

class _FixedLanguageLocalization extends LocalizationController {
  @override
  LocalizationState build() => const LocalizationState(
    setting: LocalizationSetting(
      language: 'en',
      timezone: 'UTC',
      currency: 'USD',
      dateFormat: '%Y-%m-%d %H:%M:%S',
      numberFormat: 'en_US',
      countryCode: 'US',
    ),
  );
}

AppStrings _strings() {
  final container = ProviderContainer(
    overrides: [
      localizationControllerProvider.overrideWith(
        _FixedLanguageLocalization.new,
      ),
    ],
  );
  addTearDown(container.dispose);
  return container.read(stringsProvider);
}

DioException _dio(
  int status, {
  Object? data,
  DioExceptionType type = DioExceptionType.badResponse,
}) {
  return DioException(
    requestOptions: RequestOptions(path: '/x'),
    type: type,
    response: Response(
      requestOptions: RequestOptions(path: '/x'),
      statusCode: status,
      data: data,
    ),
  );
}

void main() {
  group('friendlyError', () {
    test('maps status codes to friendly messages', () {
      final s = _strings();
      expect(friendlyError(_dio(400), s), s.of('badCredentials'));
      expect(friendlyError(_dio(403), s), s.of('forbidden'));
      expect(friendlyError(_dio(404), s), s.of('notFound'));
      expect(friendlyError(_dio(409), s), s.of('conflict'));
      expect(friendlyError(_dio(413), s), s.of('imageTooLarge'));
      expect(friendlyError(_dio(415), s), s.of('unsupportedImage'));
      expect(friendlyError(_dio(422), s), s.of('validationFailed'));
      expect(friendlyError(_dio(423), s), s.of('accountLocked'));
      expect(friendlyError(_dio(429), s), s.of('rateLimited'));
    });

    test('maps locked detail on 400', () {
      final s = _strings();
      expect(
        friendlyError(
          _dio(400, data: {'detail': 'Account temporarily locked'}),
          s,
        ),
        s.of('accountLocked'),
      );
    });

    test('maps connection failures', () {
      final s = _strings();
      expect(
        friendlyError(_dio(0, type: DioExceptionType.connectionError), s),
        s.of('cannotReachServer'),
      );
      expect(
        friendlyError(_dio(0, type: DioExceptionType.connectionTimeout), s),
        s.of('cannotReachServer'),
      );
    });

    test('falls back to generic', () {
      final s = _strings();
      expect(friendlyError(StateError('boom'), s), s.of('genericError'));
      expect(friendlyError(_dio(500), s), s.of('genericError'));
    });
  });
}
