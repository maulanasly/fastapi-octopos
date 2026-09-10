/// POS banners: pending and failed outbox rows surface above the
/// catalog with working actions.
library;

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/api_client.dart';
import 'package:octopos_client/core/api_repositories.dart';
import 'package:octopos_client/core/auth_controller.dart';
import 'package:octopos_client/core/db/app_database.dart';
import 'package:octopos_client/core/db/database_provider.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/core/sync/connectivity_provider.dart';
import 'package:octopos_client/core/sync/outbox_repository.dart';
import 'package:octopos_client/core/token_store.dart';
import 'package:octopos_client/features/pos/pos_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';

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
    email: 'cashier@octopos.test',
    fullName: 'Cashier',
    permissions: {'orders:manage', 'orders:track', 'customers:manage'},
  );
}

class _FakeSyncRepo extends SyncRepository {
  _FakeSyncRepo()
    : super(ApiClient(store: TokenStore(), onSessionExpired: () {}));

  @override
  Future<CatalogDelta> catalog({String? since}) async => const CatalogDelta(
    serverTime: '2026-08-16T10:00:00',
  );
}

class _FakeDrawer extends DrawerRepository {
  _FakeDrawer()
    : super(ApiClient(store: TokenStore(), onSessionExpired: () {}));

  @override
  Future<DrawerSession?> active() async => null;
}

ProviderContainer _container(AppDatabase db) => ProviderContainer(
  overrides: [
    localizationControllerProvider.overrideWith(
      _FixedLanguageLocalization.new,
    ),
    authControllerProvider.overrideWith(_FakeAuth.new),
    appDatabaseProvider.overrideWithValue(db),
    syncRepositoryProvider.overrideWithValue(_FakeSyncRepo()),
    drawerRepositoryProvider.overrideWithValue(_FakeDrawer()),
    connectivityProvider.overrideWith(
      (ref) => Stream.value(ConnectivityResult.wifi),
    ),
  ],
);

Future<void> _pump(WidgetTester tester, ProviderContainer container) async {
  SharedPreferences.setMockInitialValues({});
  await tester.pumpWidget(
    UncontrolledProviderScope(
      container: container,
      // PosScreen has no Scaffold of its own in production either;
      // HomeShell provides it.
      child: const MaterialApp(home: Scaffold(body: PosScreen())),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('failed outbox rows show a banner opening the review', (
    tester,
  ) async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final container = _container(db);
    addTearDown(container.dispose);

    final outbox = container.read(outboxRepositoryProvider);
    final id = await outbox.enqueueOrder(
      items: const [
        {'product_id': 1, 'quantity': 1},
      ],
    );
    await outbox.markFailed(id, 'http_422');
    await _pump(tester, container);

    expect(find.text('1 order(s) failed to sync'), findsOneWidget);

    await tester.tap(find.text('View details'));
    await tester.pumpAndSettle();

    expect(find.text('Failed orders'), findsOneWidget);
    expect(find.text('Order #$id'), findsOneWidget);
    expect(
      find.text('Please check the entered values.'),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('pending outbox rows show a retry banner', (tester) async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final container = _container(db);
    addTearDown(container.dispose);

    await container.read(outboxRepositoryProvider).enqueueOrder(
      items: const [
        {'product_id': 1, 'quantity': 1},
      ],
    );
    await _pump(tester, container);

    expect(find.text('Pending sync: 1'), findsOneWidget);
    expect(find.text('Retry'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
