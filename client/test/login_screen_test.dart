/// Login screen: validation messages resolve through strings
/// (the email validator used to return hardcoded English).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/features/auth/login_screen.dart';

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

Future<void> _pump(
  WidgetTester tester,
  ProviderContainer container,
) async {
  // Wide layout: the narrow hero column overflows short viewports.
  tester.view.devicePixelRatio = 1.0;
  tester.view.physicalSize = const Size(1280, 900);
  addTearDown(tester.view.reset);
  await tester.pumpWidget(
    UncontrolledProviderScope(
      container: container,
      child: const MaterialApp(home: LoginScreen()),
    ),
  );
  await tester.pumpAndSettle();
}

ProviderContainer _container(String language) => ProviderContainer(
  overrides: [
    localizationControllerProvider.overrideWith(
      () => _FixedLanguageLocalization(language),
    ),
  ],
);

void main() {
  testWidgets('invalid email shows the localized validator message', (
    tester,
  ) async {
    final container = _container('en');
    addTearDown(container.dispose);
    await _pump(tester, container);

    await tester.enterText(
      find.byKey(const Key('emailField')),
      'not-an-email',
    );
    await tester.tap(find.byKey(const Key('signInButton')));
    await tester.pumpAndSettle();

    expect(find.text('Valid email required'), findsOneWidget);
  });

  testWidgets('validator message follows the active locale', (tester) async {
    final container = _container('id');
    addTearDown(container.dispose);
    await _pump(tester, container);

    await tester.enterText(
      find.byKey(const Key('emailField')),
      'not-an-email',
    );
    await tester.tap(find.byKey(const Key('signInButton')));
    await tester.pumpAndSettle();

    expect(find.text('Email valid diperlukan'), findsOneWidget);
  });
}
