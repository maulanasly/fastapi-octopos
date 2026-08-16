import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/api_client.dart';
import 'package:octopos_client/core/api_repositories.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/core/token_store.dart';
import 'package:octopos_client/features/pos/cart_controller.dart';
import 'package:octopos_client/features/pos/pos_screen.dart';

class _FakeCustomers extends CustomerRepository {
  _FakeCustomers(super.api);

  final List<Customer> stored = [
    const Customer(
      id: 1,
      name: 'Alice',
      email: 'alice@example.com',
      isActive: true,
      pointsBalance: 12,
    ),
    const Customer(
      id: 2,
      name: 'Bob',
      isActive: true,
      pointsBalance: 0,
    ),
  ];

  @override
  Future<List<Customer>> list() async => stored;

  @override
  Future<Customer> create({
    required String name,
    String? email,
    String? phone,
  }) async {
    final customer = Customer(
      id: 99,
      name: name,
      email: email,
      phone: phone,
      isActive: true,
      pointsBalance: 0,
    );
    stored.add(customer);
    return customer;
  }
}

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

ProviderContainer _container() => ProviderContainer(
      overrides: [
        localizationControllerProvider
            .overrideWith(_FixedLanguageLocalization.new),
        customerRepositoryProvider.overrideWithValue(
          _FakeCustomers(
            ApiClient(store: TokenStore(), onSessionExpired: () {}),
          ),
        ),
      ],
    );

/// Pumps a host that opens the picker and forwards the pop result.
Future<void> _pumpPickerHost(
  WidgetTester tester,
  ProviderContainer container,
  void Function(dynamic result) onResult,
) async {
  await tester.pumpWidget(
    UncontrolledProviderScope(
      container: container,
      child: MaterialApp(
        home: Scaffold(
          body: Builder(
            builder: (context) => Center(
              child: ElevatedButton(
                onPressed: () async {
                  final result = await showDialog<dynamic>(
                    context: context,
                    builder: (_) => const CustomerPickerDialog(),
                  );
                  onResult(result);
                },
                child: const Text('open'),
              ),
            ),
          ),
        ),
      ),
    ),
  );
  await tester.tap(find.text('open'));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('cart defaults to guest (no customer attached)', (tester) async {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    final state = container.read(cartControllerProvider);
    expect(state.customer, isNull, reason: 'walk-in guest by default');
    expect(state.isEmpty, isTrue);
  });

  testWidgets('picker shows walk-in guest and registered customers',
      (tester) async {
    final container = _container();
    addTearDown(container.dispose);

    await _pumpPickerHost(tester, container, (_) {});

    expect(find.text('Select customer'), findsOneWidget);
    expect(find.text('Walk-in guest'), findsOneWidget);
    expect(find.text('Alice'), findsOneWidget);
    expect(find.text('Bob'), findsOneWidget);
  });

  testWidgets('walk-in guest sets customer to null', (tester) async {
    final container = _container();
    addTearDown(container.dispose);

    dynamic picked;
    await _pumpPickerHost(tester, container, (r) => picked = r);

    await tester.tap(find.text('Walk-in guest'));
    await tester.pumpAndSettle();

    expect(picked, isNotNull);
    expect(picked.customer, isNull);
  });

  testWidgets('selecting a customer returns it', (tester) async {
    final container = _container();
    addTearDown(container.dispose);

    dynamic picked;
    await _pumpPickerHost(tester, container, (r) => picked = r);

    await tester.tap(find.text('Alice'));
    await tester.pumpAndSettle();

    expect(picked, isNotNull);
    expect(picked.customer, isNotNull);
    expect(picked.customer.id, 1);
  });

  testWidgets('registering a customer creates and selects it', (tester) async {
    final container = _container();
    addTearDown(container.dispose);

    dynamic picked;
    await _pumpPickerHost(tester, container, (r) => picked = r);

    await tester.tap(find.text('Register new customer'));
    await tester.pumpAndSettle();
    await tester.enterText(
        find.widgetWithText(TextField, 'Name').first, 'Carol');
    await tester.tap(find.text('Create'));
    await tester.pumpAndSettle();

    expect(picked, isNotNull);
    expect(picked.customer, isNotNull);
    expect(picked.customer.name, 'Carol');
  });
}
