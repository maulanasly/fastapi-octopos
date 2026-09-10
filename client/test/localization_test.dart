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

    test('feedback and scope keys resolve in both languages', () {
      final en = _stringsContainer('en');
      addTearDown(en.dispose);
      final es = en.read(stringsProvider);
      expect(es.of('saved'), 'Saved');
      expect(es.of('deactivated'), 'Deactivated');
      expect(es.of('poNumber', args: {'id': 7}), 'PO #7');
      expect(es.of('scopeOrder'), 'Order');
      expect(es.of('scopeCategory'), 'Category');
      expect(es.of('scopeProduct'), 'Product');
      expect(es.of('modeExclusive'), 'Exclusive');
      expect(es.of('modeInclusive'), 'Inclusive');

      final id = _stringsContainer('id');
      addTearDown(id.dispose);
      final is_ = id.read(stringsProvider);
      expect(is_.of('saved'), 'Disimpan');
      expect(is_.of('deactivated'), 'Dinonaktifkan');
      expect(is_.of('poNumber', args: {'id': 7}), 'PO #7');
      expect(is_.of('scopeOrder'), 'Pesanan');
      expect(is_.of('scopeCategory'), 'Kategori');
      expect(is_.of('scopeProduct'), 'Produk');
      expect(is_.of('modeExclusive'), 'Eksklusif');
      expect(is_.of('modeInclusive'), 'Inklusif');
    });

    test('status, movement, and help keys resolve in both languages', () {
      final en = _stringsContainer('en');
      addTearDown(en.dispose);
      final es = en.read(stringsProvider);
      expect(es.of('statusDraft'), 'Draft');
      expect(es.of('statusOrdered'), 'Ordered');
      expect(
        es.of('statusPartiallyReceived'),
        'Partially received',
      );
      expect(es.of('statusRejected'), 'Rejected');
      expect(es.of('statusApproved'), 'Approved');
      expect(es.of('movementSale'), 'Sale');
      expect(es.of('movementManualAdjust'), 'Manual adjustment');
      expect(es.of('ledgerKindOrder'), 'Purchase order');
      expect(es.of('refundNumber', args: {'id': 3}), 'Refund #3');
      expect(es.of('reorderAt', args: {'point': 5}), 'reorder at 5');
      expect(es.of('helpStepCartHint'), contains('Guest'));
      expect(es.of('tipsOffline'), contains('Offline:'));

      final id = _stringsContainer('id');
      addTearDown(id.dispose);
      final is_ = id.read(stringsProvider);
      expect(is_.of('statusDraft'), 'Draf');
      expect(is_.of('statusOrdered'), 'Dipesan');
      expect(
        is_.of('statusPartiallyReceived'),
        'Diterima sebagian',
      );
      expect(is_.of('statusRejected'), 'Ditolak');
      expect(is_.of('statusApproved'), 'Disetujui');
      expect(is_.of('movementSale'), 'Penjualan');
      expect(is_.of('movementManualAdjust'), 'Penyesuaian manual');
      expect(is_.of('ledgerKindOrder'), 'Pesanan pembelian');
      expect(is_.of('refundNumber', args: {'id': 3}), 'Refund #3');
      expect(is_.of('reorderAt', args: {'point': 5}), 'restok di 5');
      expect(is_.of('helpStepCartHint'), contains('Tamu'));
      expect(is_.of('tipsOffline'), contains('Offline:'));
    });
  });

  _authProfileTests();

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

void _authProfileTests() {
  test('displayName prefers the full name and falls back to email', () {
    const withName = AuthState(
      status: AuthStatus.signedIn,
      email: 'cashier@example.com',
      fullName: 'Budi Cashier',
    );
    expect(withName.displayName, 'Budi Cashier');

    const emailOnly = AuthState(
      status: AuthStatus.signedIn,
      email: 'cashier@example.com',
    );
    expect(emailOnly.displayName, 'cashier@example.com');
  });

  test('UserProfile parses the /auth/me payload', () {
    final profile = UserProfile.fromJson(const {
      'id': 3,
      'email': 'cashier@example.com',
      'full_name': 'Budi Cashier',
      'is_active': true,
      'is_superuser': false,
    });
    expect(profile.fullName, 'Budi Cashier');
    expect(profile.isSuperuser, isFalse);
  });
}
