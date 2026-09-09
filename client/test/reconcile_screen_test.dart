/// Reconcile flow: an empty drawer explains itself and always offers a
/// way back to POS (a cold-started /reconcile deep link has no opener
/// to pop back to).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/features/drawer/drawer_controller.dart' as drawer;
import 'package:octopos_client/features/drawer/reconcile_screen.dart';

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

class _EmptyDrawer extends drawer.DrawerController {
  @override
  drawer.DrawerState build() => const drawer.DrawerState();
}

void main() {
  testWidgets('empty drawer explains and routes back to POS', (tester) async {
    final container = ProviderContainer(
      overrides: [
        localizationControllerProvider.overrideWith(
          _FixedLanguageLocalization.new,
        ),
        drawer.drawerControllerProvider.overrideWith(_EmptyDrawer.new),
      ],
    );
    addTearDown(container.dispose);
    // Cold-started deep link: /reconcile is the entry, so there is
    // nothing to pop — the button must go (not pop) to /pos.
    final router = GoRouter(
      initialLocation: '/reconcile',
      routes: [
        GoRoute(
          path: '/reconcile',
          builder: (context, state) => const ReconcileScreen(),
        ),
        GoRoute(
          path: '/pos',
          builder: (context, state) => const Text('POS home'),
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

    expect(
      find.text('No open drawer. Open one before taking orders.'),
      findsOneWidget,
    );
    expect(find.text('Back to POS'), findsOneWidget);

    await tester.tap(find.text('Back to POS'));
    await tester.pumpAndSettle();

    expect(find.text('POS home'), findsOneWidget);
  });
}
