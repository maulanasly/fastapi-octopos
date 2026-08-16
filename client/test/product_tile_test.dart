import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/features/pos/product_tile.dart';

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

Product _product({
  String name = 'Cafe Latte',
  String? imageUrl,
  String? categoryColor,
}) {
  return Product(
    id: 1,
    name: name,
    sku: 'LATTE-1',
    price: 4.5,
    stockQuantity: 5,
    minStock: 0,
    reorderPoint: 0,
    leadTimeDays: 0,
    imageUrl: imageUrl,
    category: categoryColor == null
        ? null
        : Category(id: 1, name: 'Beverages', color: categoryColor),
  );
}

Future<void> _pumpTile(
  WidgetTester tester, {
  Product? product,
  Size size = const Size(200, 222),
}) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        localizationControllerProvider
            .overrideWith(_FixedLanguageLocalization.new),
      ],
      child: MaterialApp(
        home: Scaffold(
          body: Center(
            child: SizedBox(
              width: size.width,
              height: size.height,
              child: ProductTile(product: product ?? _product()),
            ),
          ),
        ),
      ),
    ),
  );
  await tester.pump();
}

void main() {
  testWidgets('tile shows the product name (no overflow, no image)',
      (tester) async {
    await _pumpTile(tester);
    expect(tester.takeException(), isNull, reason: 'no overflow expected');
    expect(find.text('Cafe Latte'), findsOneWidget);
    expect(find.text(r'$4.50'), findsOneWidget);
  });

  testWidgets('tile fits a long product name without overflow',
      (tester) async {
    await _pumpTile(
      tester,
      product: _product(name: 'Extra Long Cappuccino Grande Special Blend'),
    );
    expect(tester.takeException(), isNull);
    expect(find.text('Extra Long Cappuccino Grande Special Blend'),
        findsOneWidget);
  });

  testWidgets('tile with a category color renders the tinted bar',
      (tester) async {
    await _pumpTile(
      tester,
      product: _product(categoryColor: '#D1FAE5'),
    );
    expect(tester.takeException(), isNull);
    expect(find.text('Cafe Latte'), findsOneWidget);
  });

  testWidgets('tile survives a very small slot without overflow',
      (tester) async {
    await _pumpTile(
      tester,
      size: const Size(140, 160),
    );
    expect(tester.takeException(), isNull);
    expect(find.text('Cafe Latte'), findsOneWidget);
  });
}
