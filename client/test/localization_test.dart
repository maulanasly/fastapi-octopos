import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/api_client.dart';
import 'package:octopos_client/core/api_repositories.dart';
import 'package:octopos_client/core/auth_controller.dart';
import 'package:octopos_client/core/dates.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/core/money.dart';
import 'package:octopos_client/core/strings.dart';
import 'package:octopos_client/core/token_store.dart';

class _FakeAuth extends AuthController {
  @override
  AuthState build() => const AuthState(status: AuthStatus.signedOut);
}

class _FakeLocalizationRepo extends LocalizationRepository {
  _FakeLocalizationRepo(super.api);

  LocalizationSetting current = const LocalizationSetting(
    language: 'en',
    timezone: 'UTC',
    currency: 'USD',
    dateFormat: '%Y-%m-%d %H:%M:%S',
    numberFormat: 'en_US',
    countryCode: 'US',
  );

  @override
  Future<LocalizationSetting> me() async => current;

  @override
  Future<LocalizationSetting> updateRegion(String? region) async {
    current = region == 'ID'
        ? const LocalizationSetting(
            language: 'id',
            timezone: 'Asia/Jakarta',
            currency: 'IDR',
            dateFormat: '%d-%m-%Y %H:%M',
            numberFormat: 'id_ID',
            countryCode: 'ID',
          )
        : const LocalizationSetting(
            language: 'en',
            timezone: 'UTC',
            currency: 'USD',
            dateFormat: '%Y-%m-%d %H:%M:%S',
            numberFormat: 'en_US',
            countryCode: 'US',
          );
    return current;
  }

  @override
  Future<List<LocalizationRegion>> regions() async => const [
    LocalizationRegion(
      countryCode: 'US',
      language: 'en',
      timezone: 'UTC',
      currency: 'USD',
      dateFormat: '%Y-%m-%d %H:%M:%S',
      numberFormat: 'en_US',
    ),
    LocalizationRegion(
      countryCode: 'ID',
      language: 'id',
      timezone: 'Asia/Jakarta',
      currency: 'IDR',
      dateFormat: '%d-%m-%Y %H:%M',
      numberFormat: 'id_ID',
    ),
  ];
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('money region formatting', () {
    test('US default: dollar with two decimals', () {
      configureMoney(currency: 'USD', numberFormat: 'en_US');
      expect(formatCents(450), r'$4.50');
      expect(formatCents(10000), r'$100.00');
    });

    test('IDR: rupiah, id_ID separators, no decimals', () {
      configureMoney(currency: 'IDR', numberFormat: 'id_ID');
      expect(formatCents(450000), 'Rp 4.500');
      expect(formatCents(45500), 'Rp 455');
    });

    test('extended currency symbols', () {
      configureMoney(currency: 'JPY', numberFormat: 'en_US');
      expect(formatCents(450), '¥4.50');
      configureMoney(currency: 'SGD', numberFormat: 'en_US');
      expect(formatCents(450), r'S$4.50');
    });
  });

  group('date region formatting', () {
    test('UTC keeps the ISO-style pattern', () {
      configureDates(timezone: 'UTC', dateFormat: '%Y-%m-%d %H:%M:%S');
      final dt = DateTime.utc(2026, 8, 16, 12, 30, 45);
      expect(formatDateTime(dt), '2026-08-16 12:30:45');
    });

    test('WIB (UTC+7) shifts the time and uses dd-mm-yyyy HH:MM', () {
      configureDates(timezone: 'Asia/Jakarta', dateFormat: '%d-%m-%Y %H:%M');
      final dt = DateTime.utc(2026, 8, 16, 12, 30);
      expect(formatDateTime(dt), '16-08-2026 19:30');
    });

    test('null ISO renders a placeholder', () {
      configureDates(timezone: 'UTC', dateFormat: '%Y-%m-%d %H:%M:%S');
      expect(formatDateTimeIso(null), '-');
    });
  });

  group('strings', () {
    test('english lookups resolve', () {
      final container = _stringsContainer('en');
      addTearDown(container.dispose);
      final s = container.read(stringsProvider);
      expect(s.of('checkout'), 'Checkout');
      expect(s.of('cartCount', args: {'count': 3}), 'Cart (3)');
    });

    test('indonesian lookups resolve', () {
      final container = _stringsContainer('id');
      addTearDown(container.dispose);
      expect(container.read(stringsProvider).of('checkout'), 'Bayar');
    });

    test('unknown key falls back to the key itself', () {
      final container = _stringsContainer('id');
      addTearDown(container.dispose);
      expect(
        container.read(stringsProvider).of('totallyMissing'),
        'totallyMissing',
      );
    });
  });

  group('LocalizationController', () {
    test('load applies settings and switches region', () async {
      final container = ProviderContainer(
        overrides: [
          authControllerProvider.overrideWith(_FakeAuth.new),
          localizationRepositoryProvider.overrideWithValue(
            _FakeLocalizationRepo(
              ApiClient(store: TokenStore(), onSessionExpired: () {}),
            ),
          ),
        ],
      );
      addTearDown(container.dispose);

      final notifier = container.read(localizationControllerProvider.notifier);
      await notifier.load();
      expect(
        container.read(localizationControllerProvider).setting!.currency,
        'USD',
      );

      await notifier.setRegion('ID');
      final setting = container.read(localizationControllerProvider).setting!;
      expect(setting.currency, 'IDR');
      expect(setting.countryCode, 'ID');
      expect(container.read(apiClientProvider).session.language, 'id');

      await notifier.setRegion(null);
      expect(
        container.read(localizationControllerProvider).setting!.currency,
        'USD',
      );
    });
  });
}

ProviderContainer _stringsContainer(String language) {
  return ProviderContainer(
    overrides: [
      localizationControllerProvider.overrideWith(
        () => _FixedLanguageLocalization(language),
      ),
    ],
  );
}

class _FixedLanguageLocalization extends LocalizationController {
  _FixedLanguageLocalization(this.language);

  final String language;

  @override
  LocalizationState build() => LocalizationState(
    setting: LocalizationSetting(
      language: language,
      timezone: 'UTC',
      currency: 'USD',
      dateFormat: '%Y-%m-%d %H:%M:%S',
      numberFormat: 'en_US',
      countryCode: 'US',
    ),
  );
}
