/// Home shell regression: navigation must scroll or defer instead of
/// overflowing when a user has more destinations than fit the viewport
/// (a superuser sees up to 14) — on both the wide rail and the narrow
/// bottom bar.
library;

import 'package:flutter/material.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:drift/native.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
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

class _SuperuserAuth extends AuthController {
  @override
  AuthState build() => AuthState(
    status: AuthStatus.signedIn,
    userId: 1,
    email: 'root@octopos.test',
    fullName: 'Root',
    permissions: {for (final access in kRouteAccess) ...access.anyOf},
    isSuperuser: true,
  );
}

/// `setSurfaceSize` does not drive view metrics; set them directly.
void _setLogicalSize(WidgetTester tester, Size logical) {
  tester.view.devicePixelRatio = 1.0;
  tester.view.physicalSize = logical;
  addTearDown(tester.view.reset);
}

Future<void> _pumpShell(WidgetTester tester) async {
  SharedPreferences.setMockInitialValues({});
  final db = AppDatabase.forTesting(NativeDatabase.memory());
  addTearDown(db.close);
  final container = ProviderContainer(
    overrides: [
      localizationControllerProvider.overrideWith(
        _FixedLanguageLocalization.new,
      ),
      authControllerProvider.overrideWith(_SuperuserAuth.new),
      // The region menu hits the API; without an override its error-retry
      // timer outlives the test (pending-timer invariant).
      regionListProvider.overrideWith((ref) async => <LocalizationRegion>[]),
      appDatabaseProvider.overrideWithValue(db),
      connectivityProvider.overrideWith((ref) => Stream.value(ConnectivityResult.wifi)),
    ],
  );
  addTearDown(container.dispose);
  await tester.pumpWidget(
    UncontrolledProviderScope(container: container, child: const OctoPosApp()),
  );
  await tester.pumpAndSettle();
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('rail scrolls instead of overflowing with many destinations', (
    tester,
  ) async {
    // Wide enough for the rail (>=840), too short for 14 labeled
    // destinations — this overflowed vertically before the fix.
    _setLogicalSize(tester, const Size(1100, 600));
    await _pumpShell(tester);

    expect(tester.takeException(), isNull);
    expect(find.byType(NavigationRail), findsOneWidget);
    expect(find.text('Serving'), findsOneWidget);

    // The primary regression guard is the absence of a vertical overflow
    // exception above; dragging must also be safe when content exceeds
    // the viewport (exact label visibility depends on text metrics).
    await tester.drag(find.byType(NavigationRail), const Offset(0, -500));
    await tester.pumpAndSettle();

    expect(find.byType(NavigationRail), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('rail fills tall viewports without needing to scroll', (
    tester,
  ) async {
    _setLogicalSize(tester, const Size(1100, 1400));
    await _pumpShell(tester);

    expect(tester.takeException(), isNull);
    expect(find.byType(NavigationRail), findsOneWidget);
    expect(find.text('Serving'), findsOneWidget);
    // Everything fits: even the last destination is already visible.
    expect(find.text('Reports'), findsOneWidget);
  });

  testWidgets('bottom bar defers extra destinations behind More', (
    tester,
  ) async {
    // Below the 840px cutoff the shell swaps the rail for a bottom bar;
    // 14 destinations overflowed it horizontally before the fix.
    await _pumpShell(tester); // default surface: 800x600 (narrow)

    expect(tester.takeException(), isNull);
    expect(find.byType(NavigationBar), findsOneWidget);
    expect(find.text('Serving'), findsOneWidget);

    // Hidden destinations live in the More sheet.
    await tester.tap(find.text('More'));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);

    // The sheet list is lazy: scroll far enough to build the later tiles.
    await tester.drag(find.byType(BottomSheet), const Offset(0, -500));
    await tester.pumpAndSettle();

    // Deferred destinations are reachable in the sheet (their screens'
    // behaviour has dedicated suites; navigating here would fan out API
    // calls irrelevant to the shell).
    expect(find.text('Reports'), findsOneWidget);
    expect(find.text('Staff'), findsOneWidget);

    // Dismiss via the modal barrier.
    await tester.tapAt(const Offset(20, 300));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  });
}
