import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/api_client.dart';
import 'package:octopos_client/core/api_repositories.dart';
import 'package:octopos_client/core/auth_controller.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/core/token_store.dart';
import 'package:octopos_client/features/taxes/taxes_screen.dart';

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
    permissions: {'taxes:manage'},
  );
}

class _FakeTaxes extends TaxRepository {
  _FakeTaxes() : super(ApiClient(store: TokenStore(), onSessionExpired: () {}));

  bool created = false;

  @override
  Future<List<TaxRule>> list() async => const [
    TaxRule(
      id: 1,
      name: 'VAT',
      taxScope: 'order',
      taxMode: 'exclusive',
      rate: 11,
      isActive: true,
    ),
  ];

  @override
  Future<TaxRule> create(Map<String, dynamic> body) async {
    created = true;
    return TaxRule(
      id: 2,
      name: body['name'] as String,
      taxScope: body['tax_scope'] as String,
      taxMode: body['tax_mode'] as String,
      rate: (body['rate'] as num).toDouble(),
      isActive: body['is_active'] as bool,
    );
  }
}

ProviderContainer _container() => ProviderContainer(
  overrides: [
    localizationControllerProvider.overrideWith(_FixedLanguageLocalization.new),
    authControllerProvider.overrideWith(_FakeAuth.new),
    taxRepositoryProvider.overrideWithValue(_FakeTaxes()),
  ],
);

Future<void> _pump(WidgetTester tester, ProviderContainer container) async {
  await tester.pumpWidget(
    UncontrolledProviderScope(
      container: container,
      child: const MaterialApp(home: TaxesScreen()),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('lists tax rules with rate', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pump(tester, container);

    expect(find.textContaining('VAT'), findsOneWidget);
    expect(find.textContaining('%'), findsWidgets);
    expect(find.textContaining('order · exclusive'), findsOneWidget);
  });

  testWidgets('create tax rule dialog posts a new rule', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    final fake = container.read(taxRepositoryProvider) as _FakeTaxes;
    await _pump(tester, container);

    await tester.tap(find.byType(FloatingActionButton));
    await tester.pumpAndSettle();

    await tester.enterText(find.widgetWithText(TextField, 'Tax name'), 'GST');
    await tester.enterText(find.widgetWithText(TextField, 'Rate'), '10');
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    expect(fake.created, isTrue);
  });
}
