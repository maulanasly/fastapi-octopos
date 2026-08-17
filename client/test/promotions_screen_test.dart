import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/api_client.dart';
import 'package:octopos_client/core/api_repositories.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/core/token_store.dart';
import 'package:octopos_client/features/promotions/promotions_screen.dart';

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

class _FakePromotions extends PromotionRepository {
  _FakePromotions()
    : super(ApiClient(store: TokenStore(), onSessionExpired: () {}));

  List<Promotion> stored = const [
    Promotion(
      id: 1,
      code: 'SAVE10',
      name: 'Save 10',
      description: '10% off',
      discountType: 'percentage',
      discountValue: 10,
      minOrderAmount: 0,
      appliesTo: 'order',
      isActive: true,
      usageCount: 3,
    ),
    Promotion(
      id: 2,
      code: 'FLAT2',
      name: 'Flat 2',
      discountType: 'fixed',
      discountValue: 2,
      minOrderAmount: 10,
      appliesTo: 'category',
      categoryId: 1,
      isActive: false,
      usageCount: 0,
    ),
  ];
  int deactivated = 0;

  @override
  Future<List<Promotion>> list() async => stored;

  @override
  Future<void> deactivate(int id) async {
    deactivated++;
    stored = stored.map((p) {
      if (p.id == id) {
        return Promotion(
          id: p.id,
          code: p.code,
          name: p.name,
          description: p.description,
          discountType: p.discountType,
          discountValue: p.discountValue,
          minOrderAmount: p.minOrderAmount,
          maxDiscountAmount: p.maxDiscountAmount,
          appliesTo: p.appliesTo,
          productId: p.productId,
          categoryId: p.categoryId,
          isActive: false,
          usageLimit: p.usageLimit,
          usageCount: p.usageCount,
        );
      }
      return p;
    }).toList();
  }
}

ProviderContainer _container() => ProviderContainer(
  overrides: [
    localizationControllerProvider.overrideWith(_FixedLanguageLocalization.new),
    promotionRepositoryProvider.overrideWithValue(_FakePromotions()),
  ],
);

Future<void> _pump(WidgetTester tester, ProviderContainer container) async {
  await tester.pumpWidget(
    UncontrolledProviderScope(
      container: container,
      child: const MaterialApp(home: PromotionsScreen()),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('lists promotions with type and usage', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pump(tester, container);

    expect(find.text('SAVE10 — Save 10'), findsOneWidget);
    expect(find.textContaining('10.0%'), findsOneWidget);
    expect(find.textContaining('order ·'), findsOneWidget);
    expect(find.textContaining('Used 3 times'), findsOneWidget);
    expect(find.text('FLAT2 — Flat 2'), findsOneWidget);
    expect(find.textContaining(r'$2.00'), findsOneWidget);
  });

  testWidgets('deactivate confirms and refreshes', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pump(tester, container);

    await tester.tap(find.byIcon(Icons.remove_circle_outline));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Deactivate').last);
    await tester.pumpAndSettle();

    final fake = container.read(promotionRepositoryProvider) as _FakePromotions;
    expect(fake.deactivated, 1);
    expect(fake.stored.first.isActive, isFalse);
  });

  testWidgets('create dialog opens', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pump(tester, container);

    await tester.tap(find.byIcon(Icons.add));
    await tester.pumpAndSettle();

    expect(find.text('New promotion'), findsOneWidget);
    expect(find.text('Discount type'), findsOneWidget);
    expect(find.text('Percentage'), findsOneWidget);
    expect(find.text('Fixed amount'), findsOneWidget);
  });
}
