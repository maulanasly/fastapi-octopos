/// Navigation-flow regression: denied routes announce themselves,
/// unknown routes show a real 404, and receipt IDs are validated.
library;

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:drift/native.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/app/router.dart';
import 'package:octopos_client/core/api_repositories.dart';
import 'package:octopos_client/core/auth_controller.dart';
import 'package:octopos_client/core/db/app_database.dart';
import 'package:octopos_client/core/db/database_provider.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/core/route_access.dart';
import 'package:octopos_client/core/sync/connectivity_provider.dart';
import 'package:octopos_client/main.dart';
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

/// Cashier without admin (or any manage) permission.
class _CashierAuth extends AuthController {
  @override
  AuthState build() => const AuthState(
    status: AuthStatus.signedIn,
    userId: 2,
    email: 'cashier@octopos.test',
    fullName: 'Cashier',
    permissions: {'orders:manage', 'orders:track'},
  );
}

Future<ProviderContainer> _pumpApp(WidgetTester tester) async {
  SharedPreferences.setMockInitialValues({});
  final db = AppDatabase.forTesting(NativeDatabase.memory());
  addTearDown(db.close);
  final container = ProviderContainer(
    overrides: [
      localizationControllerProvider.overrideWith(
        _FixedLanguageLocalization.new,
      ),
      authControllerProvider.overrideWith(_CashierAuth.new),
      regionListProvider.overrideWith((ref) async => <LocalizationRegion>[]),
      appDatabaseProvider.overrideWithValue(db),
      connectivityProvider.overrideWith(
        (ref) => Stream.value(ConnectivityResult.wifi),
      ),
    ],
  );
  addTearDown(container.dispose);
  await tester.pumpWidget(
    UncontrolledProviderScope(container: container, child: const OctoPosApp()),
  );
  await tester.pumpAndSettle();
  return container;
}

void main() {
  testWidgets('denied route falls back to POS with a notice', (tester) async {
    final container = await _pumpApp(tester);

    container.read(routerProvider).go('/admin');
    // Let the redirect + post-frame SnackBar land, but don't settle
    // past the SnackBar's 4s auto-dismiss.
    await tester.pump();
    await tester.pump(const Duration(seconds: 1));

    expect(find.text('You do not have permission to do that.'), findsOneWidget);
    // Fallback target is the POS catalog search field.
    expect(find.text('Search products…'), findsOneWidget);
  });

  testWidgets('unknown route shows the 404 screen with a way out', (
    tester,
  ) async {
    final container = await _pumpApp(tester);

    container.read(routerProvider).go('/nope');
    await tester.pumpAndSettle();

    expect(find.text('Page not found'), findsWidgets);
    await tester.tap(find.text('Back to POS'));
    await tester.pumpAndSettle();

    expect(find.text('Search products…'), findsOneWidget);
  });

  testWidgets('invalid receipt ID shows the 404 screen', (tester) async {
    final container = await _pumpApp(tester);

    container.read(routerProvider).go('/receipt/abc');
    await tester.pumpAndSettle();

    expect(find.text('Page not found'), findsWidgets);
  });

  testWidgets('invalid tracking ID shows the 404 screen', (tester) async {
    final container = await _pumpApp(tester);

    container.read(routerProvider).go('/tracking/abc');
    await tester.pumpAndSettle();

    expect(find.text('Page not found'), findsWidgets);
  });

  test('receipt route stays open to signed-in roles by explicit rule', () {
    const auth = AuthState(
      status: AuthStatus.signedIn,
      userId: 2,
      email: 'cashier@octopos.test',
      fullName: 'Cashier',
      permissions: {'orders:manage', 'orders:track'},
    );
    expect(routePermitted(auth, '/receipt/7'), isTrue);
    expect(routePermitted(auth, '/receipt/abc'), isTrue);
    // And the guard still closes what it should.
    expect(routePermitted(auth, '/admin'), isFalse);
  });

  testWidgets('zero and negative receipt IDs show the 404 screen', (
    tester,
  ) async {
    final container = await _pumpApp(tester);

    container.read(routerProvider).go('/receipt/0');
    await tester.pumpAndSettle();
    expect(find.text('Page not found'), findsWidgets);

    container.read(routerProvider).go('/receipt/-5');
    await tester.pumpAndSettle();
    expect(find.text('Page not found'), findsWidgets);
  });
}
