/// Help screen: step subtitles and tips resolve through strings in
/// both locales (they used to be hardcoded English).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/features/help/help_screen.dart';

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
  await tester.pumpWidget(
    UncontrolledProviderScope(
      container: container,
      child: const MaterialApp(home: HelpScreen()),
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
  testWidgets('english hints and tips render', (tester) async {
    final container = _container('en');
    addTearDown(container.dispose);
    await _pump(tester, container);

    expect(
      find.text(
        'Open drawer → enter starting cash → Checkout unlocks',
      ),
      findsOneWidget,
    );
    expect(find.text('Tips'), findsOneWidget);
    expect(
      find.textContaining('cached catalog still works'),
      findsOneWidget,
    );
  });

  testWidgets('indonesian hints and tips render', (tester) async {
    final container = _container('id');
    addTearDown(container.dispose);
    await _pump(tester, container);

    expect(
      find.text(
        'Buka laci → masukkan uang awal → Checkout terbuka',
      ),
      findsOneWidget,
    );
    expect(find.text('Tips'), findsOneWidget);
    expect(
      find.textContaining('katalog cache tetap jalan'),
      findsOneWidget,
    );
    // No leftover hardcoded English subtitles.
    expect(find.text('Open drawer → enter starting cash'), findsNothing);
  });
}
