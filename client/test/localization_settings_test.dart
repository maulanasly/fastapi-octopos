import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/api_client.dart';
import 'package:octopos_client/core/api_repositories.dart';
import 'package:octopos_client/core/auth_controller.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/core/token_store.dart';
import 'package:octopos_client/features/settings/localization_settings_screen.dart';

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

class _FakeAuth extends AuthController {
  @override
  AuthState build() => const AuthState(
    status: AuthStatus.signedIn,
    userId: 1,
    email: 'manager@example.com',
    permissions: {'settings:manage'},
  );
}

class _FakeLocalizationRepo extends LocalizationRepository {
  _FakeLocalizationRepo()
      : super(ApiClient(store: TokenStore(), onSessionExpired: () {}));

  LocalizationSetting current = const LocalizationSetting(
    language: 'en',
    timezone: 'UTC',
    currency: 'USD',
    dateFormat: '%Y-%m-%d %H:%M:%S',
    numberFormat: 'en_US',
    countryCode: 'US',
  );

  Map<String, dynamic>? saved;
  Object? error;

  @override
  Future<LocalizationSetting> settings() async => current;

  @override
  Future<LocalizationSetting> updateSettings(Map<String, dynamic> body) async {
    if (error != null) throw error!;
    saved = body;
    return current;
  }

  @override
  Future<LocalizationOptions> options() async =>
      const LocalizationOptions(
        languages: ['en', 'id'],
        currencies: ['USD', 'IDR', 'EUR'],
        timezones: ['UTC', 'Asia/Jakarta'],
        dateFormats: ['%Y-%m-%d %H:%M:%S', '%d-%m-%Y %H:%M'],
        numberFormats: ['en_US', 'id_ID'],
        countryCodes: ['US', 'ID'],
      );

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

Future<void> _pump(WidgetTester tester, _FakeLocalizationRepo repo) async {
  final container = ProviderContainer(
    overrides: [
      localizationControllerProvider.overrideWith(
        _FixedLanguageLocalization.new,
      ),
      authControllerProvider.overrideWith(_FakeAuth.new),
      localizationRepositoryProvider.overrideWithValue(repo),
    ],
  );
  addTearDown(container.dispose);
  await tester.pumpWidget(
    UncontrolledProviderScope(
      container: container,
      child: const MaterialApp(home: LocalizationSettingsScreen()),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('prefills dropdowns from the loaded setting', (tester) async {
    final repo = _FakeLocalizationRepo();
    await _pump(tester, repo);

    expect(find.text('USD · \$'), findsOneWidget);
    expect(find.text('UTC'), findsOneWidget);
    expect(find.text('2026-08-19 14:30:00'), findsOneWidget);
    expect(find.byType(DropdownButtonFormField<String>), findsNWidgets(7));
  });

  testWidgets('preset fills all fields', (tester) async {
    final repo = _FakeLocalizationRepo();
    await _pump(tester, repo);

    await tester.tap(find.text('Preset'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('ID · id · Rp').last);
    await tester.pumpAndSettle();

    expect(find.text('id'), findsOneWidget);
    expect(find.text('IDR · Rp'), findsOneWidget);
    expect(find.text('Asia/Jakarta'), findsOneWidget);
  });

  testWidgets('save sends the selected values', (tester) async {
    final repo = _FakeLocalizationRepo();
    await _pump(tester, repo);

    await tester.tap(find.text('USD · \$'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('EUR · €').last);
    await tester.pumpAndSettle();

    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    expect(repo.saved, isNotNull);
    expect(repo.saved!['currency'], 'EUR');
    expect(repo.saved!['language'], 'en');
    expect(repo.saved!['timezone'], 'UTC');
    expect(find.text('Settings saved'), findsOneWidget);
  });

  testWidgets('save error shows the friendly snackbar', (tester) async {
    final repo = _FakeLocalizationRepo()..error = Exception('boom');
    await _pump(tester, repo);

    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    expect(find.textContaining('Something went wrong'), findsOneWidget);
  });
}
