/// Products regression: saving a product confirms with a snackbar
/// (the save path used to reload silently).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/api_client.dart';
import 'package:octopos_client/core/api_repositories.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/core/pagination.dart';
import 'package:octopos_client/core/token_store.dart';
import 'package:octopos_client/features/catalog/products_screen.dart';
import 'package:octopos_client/features/pos/catalog_controller.dart';

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

class _FakeCatalog extends CatalogRepository {
  _FakeCatalog()
    : super(ApiClient(store: TokenStore(), onSessionExpired: () {}));

  int saves = 0;

  @override
  Future<List<Product>> products({
    PaginationParams pagination = PaginationParams.catalog,
  }) async => const [
    Product(id: 3, name: 'Beans', sku: 'BEAN-1', price: 15.0),
  ];

  @override
  Future<Product> createProduct(Map<String, dynamic> body) async {
    saves++;
    return Product(
      id: 4,
      name: (body['name'] ?? '') as String,
      sku: (body['sku'] ?? '') as String,
      price: ((body['price'] ?? 0) as num).toDouble(),
    );
  }
}

class _StaticCatalog extends CatalogController {
  @override
  CatalogState build() => const CatalogState(
    products: [Product(id: 3, name: 'Beans', sku: 'BEAN-1', price: 15.0)],
    loading: false,
  );

  @override
  Future<void> refresh() async {}
}

void main() {
  testWidgets('saving a product confirms with a snackbar', (tester) async {
    final fake = _FakeCatalog();
    final container = ProviderContainer(
      overrides: [
        localizationControllerProvider.overrideWith(
          _FixedLanguageLocalization.new,
        ),
        catalogRepositoryProvider.overrideWithValue(fake),
        catalogControllerProvider.overrideWith(_StaticCatalog.new),
      ],
    );
    addTearDown(container.dispose);
    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: const MaterialApp(home: ProductsScreen()),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byType(FloatingActionButton));
    await tester.pumpAndSettle();

    await tester.enterText(find.widgetWithText(TextField, 'Name'), 'Tea');
    await tester.enterText(find.widgetWithText(TextField, 'SKU'), 'TEA-1');
    await tester.enterText(find.widgetWithText(TextField, 'Price'), '2.5');
    await tester.tap(find.text('Save'));
    // Let the SnackBar land, but don't settle past its 4s auto-dismiss.
    await tester.pump();
    await tester.pump(const Duration(seconds: 1));

    expect(fake.saves, 1);
    expect(tester.takeException(), isNull);
    expect(find.text('Saved'), findsOneWidget);
  });
}
