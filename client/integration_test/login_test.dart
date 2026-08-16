/// Real-browser integration test: boots the actual app and logs in against
/// the live backend. Run with:
///   flutter drive --driver=test_driver/integration_test.dart \
///     --target=integration_test/login_test.dart -d chrome
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:octopos_client/main.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('real app: login against live backend', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: OctoPosApp()));
    await tester.pumpAndSettle(const Duration(seconds: 2));

    final emailField = find.byKey(const Key('emailField'));
    expect(emailField, findsOneWidget, reason: 'login screen should show');

    await tester.tap(emailField);
    await tester.pump(const Duration(milliseconds: 200));
    await tester.enterText(emailField, 'browser@example.com');
    await tester.tap(find.byKey(const Key('passwordField')));
    await tester.pump(const Duration(milliseconds: 200));
    await tester.enterText(find.byKey(const Key('passwordField')), 'TestPass123');
    await tester.tap(find.byKey(const Key('signInButton')));

    var posShown = false;
    String? visibleError;
    for (var i = 0; i < 40; i++) {
      await tester.pump(const Duration(milliseconds: 500));
      if (find.textContaining('Cart').evaluate().isNotEmpty) {
        posShown = true;
        break;
      }
      for (final probe in ['Could not reach', 'Incorrect', 'locked', 'Missing', 'XMLHttpRequest', 'DioException']) {
        if (find.textContaining(probe).evaluate().isNotEmpty) {
          visibleError = probe;
          break;
        }
      }
      if (visibleError != null) break;
    }

    if (visibleError != null) {
      final texts = tester
          .widgetList<Text>(find.byType(Text))
          .map((t) => t.data)
          .whereType<String>()
          .where((t) => t.isNotEmpty)
          .toList();
      // ignore: avoid_print
      print('ERROR DETECTED ($visibleError). Visible texts: $texts');
    }

    expect(posShown, isTrue,
        reason: 'POS screen should appear after login (visibleError=$visibleError)');
  });
}
