/// Customers regression: saves refresh the list (the reload closure
/// must not return a Future to setState), and navigating away mid-save
/// must not crash on a disposed State.
library;

import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:octopos_client/core/api_client.dart';
import 'package:octopos_client/core/api_repositories.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/core/token_store.dart';
import 'package:octopos_client/features/customers/customers_screen.dart';

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

class _FakeCustomers extends CustomerRepository {
  _FakeCustomers()
    : super(ApiClient(store: TokenStore(), onSessionExpired: () {}));

  List<Customer> stored = const [
    Customer(
      id: 1,
      name: 'Ada',
      email: 'ada@test',
      isActive: true,
      pointsBalance: 10,
    ),
  ];
  Completer<void>? gate;
  int creates = 0;
  bool failList = false;

  @override
  Future<List<Customer>> list() async {
    if (failList) {
      throw DioException(
        requestOptions: RequestOptions(path: '/customers/'),
        type: DioExceptionType.connectionError,
      );
    }
    return stored;
  }

  @override
  Future<Customer> create({
    required String name,
    String? email,
    String? phone,
  }) async {
    if (gate != null) await gate!.future;
    creates++;
    final created = Customer(
      id: 2,
      name: name,
      email: email,
      phone: phone,
      isActive: true,
      pointsBalance: 0,
    );
    stored = [...stored, created];
    return created;
  }
}

ProviderContainer _container(_FakeCustomers fake) => ProviderContainer(
  overrides: [
    localizationControllerProvider.overrideWith(
      _FixedLanguageLocalization.new,
    ),
    customerRepositoryProvider.overrideWithValue(fake),
  ],
);

Future<void> _startCreate(WidgetTester tester) async {
  await tester.tap(find.byType(FloatingActionButton));
  await tester.pumpAndSettle();

  final fields = find.descendant(
    of: find.byType(AlertDialog),
    matching: find.byType(TextField),
  );
  await tester.enterText(fields.at(0), 'Bob');
  await tester.tap(find.text('Create'));
}

void main() {
  testWidgets('creating a customer refreshes the list', (tester) async {
    final fake = _FakeCustomers();
    final container = _container(fake);
    addTearDown(container.dispose);
    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: const MaterialApp(home: CustomersScreen()),
      ),
    );
    await tester.pumpAndSettle();

    await _startCreate(tester);
    // Let the SnackBar land, but don't settle past its 4s auto-dismiss.
    await tester.pump();
    await tester.pump(const Duration(seconds: 1));

    expect(fake.creates, 1);
    expect(tester.takeException(), isNull);
    expect(find.text('Saved'), findsOneWidget);
    expect(find.text('Bob'), findsOneWidget);
  });

  testWidgets('failed load shows a friendly error with retry', (
    tester,
  ) async {
    final fake = _FakeCustomers()..failList = true;
    final container = _container(fake);
    addTearDown(container.dispose);
    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: const MaterialApp(home: CustomersScreen()),
      ),
    );
    await tester.pumpAndSettle();

    expect(
      find.text('Could not reach the server. Is the backend running?'),
      findsOneWidget,
    );

    fake.failList = false;
    await tester.tap(find.text('Retry'));
    await tester.pumpAndSettle();

    expect(find.text('Ada'), findsOneWidget);
  });

  testWidgets('navigating away mid-save does not crash', (tester) async {
    final fake = _FakeCustomers()..gate = Completer<void>();
    final container = _container(fake);
    addTearDown(container.dispose);
    final router = GoRouter(
      initialLocation: '/customers',
      routes: [
        GoRoute(
          path: '/customers',
          builder: (context, state) => const CustomersScreen(),
        ),
        GoRoute(
          path: '/other',
          builder: (context, state) => const Text('other'),
        ),
      ],
    );
    addTearDown(router.dispose);
    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: MaterialApp.router(routerConfig: router),
      ),
    );
    await tester.pumpAndSettle();

    await _startCreate(tester);
    await tester.pump();
    // Leave while the save is still in flight.
    router.go('/other');
    await tester.pumpAndSettle();
    fake.gate!.complete();
    await tester.pumpAndSettle();

    expect(fake.creates, 1);
    expect(tester.takeException(), isNull);
    expect(find.text('other'), findsOneWidget);
  });
}
