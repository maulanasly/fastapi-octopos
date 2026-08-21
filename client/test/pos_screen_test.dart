/// POS screen UX regressions: the draft cart survives opening a drawer,
/// barcode-style scan adds land in the cart with feedback, and misses are
/// reported instead of silently ignored.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/api_client.dart';
import 'package:octopos_client/core/api_repositories.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/core/strings.dart';
import 'package:octopos_client/core/token_store.dart';
import 'package:octopos_client/features/drawer/drawer_controller.dart';
import 'package:octopos_client/features/pos/cart_controller.dart';
import 'package:octopos_client/features/pos/catalog_controller.dart';
import 'package:octopos_client/features/pos/pos_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';

Product _product(int id, String name, {int stock = 10}) => Product(
  id: id,
  name: name,
  sku: 'SKU-$id',
  price: 4.5,
  stockQuantity: stock,
  minStock: 0,
  reorderPoint: 0,
  leadTimeDays: 0,
);

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

class _SeededCatalog extends CatalogController {
  _SeededCatalog(this.products);

  final List<Product> products;

  @override
  CatalogState build() =>
      CatalogState(categories: const [], products: products, loading: false);
}

class _FakeDrawers extends DrawerRepository {
  _FakeDrawers(super.api);

  DrawerSession? opened;

  @override
  Future<DrawerSession?> active() async => null;

  @override
  Future<DrawerSession> open({required int startingCashCents}) async {
    opened = DrawerSession(
      id: 7,
      userId: 1,
      startingCash: startingCashCents / 100,
      expectedCash: startingCashCents / 100,
      status: 'open',
      openedAt: '2026-08-21T10:00:00',
    );
    return opened!;
  }
}

/// Tests render with the monospace Ahem font, so long labels are much
/// wider than any real typeface; use a landscape-tablet surface that
/// matches real POS hardware instead of shrinking the layout.
void _setLogicalSize(WidgetTester tester) {
  tester.view.devicePixelRatio = 1.0;
  tester.view.physicalSize = const Size(1280, 800);
  addTearDown(tester.view.reset);
}

Future<ProviderContainer> _pumpPos(WidgetTester tester) async {
  _setLogicalSize(tester);
  SharedPreferences.setMockInitialValues({});
  final container = ProviderContainer(
    overrides: [
      localizationControllerProvider.overrideWith(
        _FixedLanguageLocalization.new,
      ),
      catalogControllerProvider.overrideWith(
        () => _SeededCatalog([_product(1, 'Latte'), _product(2, 'Mocha')]),
      ),
      drawerRepositoryProvider.overrideWithValue(
        _FakeDrawers(ApiClient(store: TokenStore(), onSessionExpired: () {})),
      ),
    ],
  );
  addTearDown(container.dispose);
  await tester.pumpWidget(
    UncontrolledProviderScope(
      container: container,
      child: const MaterialApp(home: Scaffold(body: PosScreen())),
    ),
  );
  await tester.pumpAndSettle();
  return container;
}

void main() {
  testWidgets('opening a drawer keeps the draft cart', (tester) async {
    final container = await _pumpPos(tester);
    container
        .read(cartControllerProvider.notifier)
        .addProduct(_product(1, 'Latte'));
    await tester.pumpAndSettle();

    // The no-drawer banner offers opening one; take it.
    await tester.tap(find.descendant(
      of: find.byType(MaterialBanner),
      matching: find.text('Open drawer'),
    ));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.descendant(of: find.byType(AlertDialog), matching: find.byType(TextField)),
      '50',
    );
    await tester.pump();
    await tester.tap(find.descendant(
      of: find.byType(AlertDialog),
      matching: find.byType(FilledButton),
    ));
    await tester.pumpAndSettle();

    // Drawer is now open...
    expect(container.read(drawerControllerProvider).session, isNotNull);
    // ...and the draft cart survived (regression: it used to be wiped).
    expect(container.read(cartControllerProvider).lines.keys, [1]);
  });

  testWidgets('scan hit adds the product to the cart', (tester) async {
    final container = await _pumpPos(tester);

    await tester.showKeyboard(find.byType(TextField).first);
    await tester.enterText(find.byType(TextField).first, 'latte');
    await tester.testTextInput.receiveAction(TextInputAction.search);
    await tester.pumpAndSettle();

    expect(container.read(cartControllerProvider).lines.keys, [1]);
    expect(
      find.text(container.read(stringsProvider).of('scanNoMatch')),
      findsNothing,
    );
  });

  testWidgets('scan miss reports instead of failing silently', (tester) async {
    final container = await _pumpPos(tester);

    await tester.showKeyboard(find.byType(TextField).first);
    await tester.enterText(find.byType(TextField).first, 'unknown-sku');
    await tester.testTextInput.receiveAction(TextInputAction.search);
    await tester.pumpAndSettle();

    expect(container.read(cartControllerProvider).lines, isEmpty);
    expect(
      find.textContaining('No product matches'),
      findsOneWidget,
    );
  });
}
