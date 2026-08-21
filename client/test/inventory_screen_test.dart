import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/api_client.dart';
import 'package:octopos_client/core/api_repositories.dart';
import 'package:octopos_client/core/auth_controller.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/core/token_store.dart';
import 'package:octopos_client/features/inventory/inventory_screen.dart';

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

class _FakeAuth extends AuthController {
  final Set<String> extraPermissions;

  _FakeAuth({this.extraPermissions = const {}});

  @override
  AuthState build() => AuthState(
    status: AuthStatus.signedIn,
    email: 'manager@example.com',
    permissions: {'inventory:view', 'products:manage', ...extraPermissions},
  );
}

class _FakeInventory extends InventoryRepository {
  _FakeInventory()
    : super(ApiClient(store: TokenStore(), onSessionExpired: () {}));

  int suggestionsCalls = 0;

  @override
  Future<List<StockMovement>> movements({
    int? productId,
    String? movementType,
    int limit = 100,
  }) async {
    final all = [
      const StockMovement(
        id: 1,
        productId: 3,
        movementType: 'sale',
        quantityBefore: 10,
        quantityDelta: -2,
        quantityAfter: 8,
        note: 'latte sold',
        createdAt: '2026-08-16T10:00:00',
      ),
      const StockMovement(
        id: 2,
        productId: 4,
        movementType: 'manual_adjustment',
        quantityBefore: 5,
        quantityDelta: 3,
        quantityAfter: 8,
        createdAt: '2026-08-16T11:00:00',
      ),
    ];
    return all
        .where((m) => movementType == null || m.movementType == movementType)
        .toList();
  }

  @override
  Future<List<ReplenishmentSuggestion>> suggestions({
    int lookbackDays = 30,
    bool onlyReorder = true,
  }) async {
    suggestionsCalls++;
    return const [
      ReplenishmentSuggestion(
        productId: 3,
        productName: 'Cafe Latte',
        sku: 'LATTE-1',
        currentStock: 2,
        minStock: 5,
        reorderPoint: 5,
        leadTimeDays: 3,
        soldQuantity: 40,
        projectedStockAtLeadTime: 1,
        recommendedOrderQuantity: 8,
        shouldReorder: true,
        unitCost: 4.5,
      ),
    ];
  }
}

class _FakePurchasing extends PurchasingRepository {
  _FakePurchasing()
    : super(ApiClient(store: TokenStore(), onSessionExpired: () {}));

  List<Map<String, dynamic>>? lastItems;

  @override
  Future<List<Supplier>> suppliers() async => const [
    Supplier(id: 7, name: 'Acme Supplies', isActive: true),
  ];

  @override
  Future<BatchReplenishmentResult> batchGenerateFromSuggestions({
    int lookbackDays = 30,
    List<Map<String, dynamic>> items = const [],
  }) async {
    lastItems = items;
    return BatchReplenishmentResult(
      purchaseOrders: const [
        PurchaseOrder(
          id: 11,
          supplierId: 7,
          userId: 1,
          status: 'draft',
          totalEstimatedAmount: 22.5,
        ),
      ],
      skipped: const [SkippedProduct(productId: 4, reason: 'no supplier history')],
    );
  }
}

ProviderContainer _container({_FakePurchasing? purchasing}) =>
    ProviderContainer(
      overrides: [
        localizationControllerProvider.overrideWith(
          _FixedLanguageLocalization.new,
        ),
        authControllerProvider.overrideWith(
          () => _FakeAuth(extraPermissions: {'purchasing:manage'}),
        ),
        inventoryRepositoryProvider.overrideWithValue(_FakeInventory()),
        purchasingRepositoryProvider.overrideWithValue(
          purchasing ?? _FakePurchasing(),
        ),
      ],
    );

Future<void> _pump(WidgetTester tester, ProviderContainer container) async {
  await tester.pumpWidget(
    UncontrolledProviderScope(
      container: container,
      child: const MaterialApp(home: InventoryScreen()),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('shows stock movements with deltas', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pump(tester, container);

    expect(find.text('Product #3 · sale'), findsOneWidget);
    expect(find.textContaining('10 → 8 (-2)'), findsOneWidget);
    expect(find.text('Product #4 · manual_adjustment'), findsOneWidget);
    expect(find.textContaining('5 → 8 (+3)'), findsOneWidget);
  });

  testWidgets('movement type filter narrows the list', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pump(tester, container);

    await tester.tap(find.text('sale'));
    await tester.pumpAndSettle();

    expect(find.text('Product #3 · sale'), findsOneWidget);
    expect(find.text('Product #4 · manual_adjustment'), findsNothing);
  });

  testWidgets('replenishment tab shows editable suggestion rows', (
    tester,
  ) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pump(tester, container);

    await tester.tap(find.text('Replenishment'));
    await tester.pumpAndSettle();

    expect(find.text('Cafe Latte'), findsOneWidget);
    // qty prefilled with the recommended quantity, cost with product price
    expect(
      tester.widget<TextField>(find.byType(TextField).first).controller!.text,
      '8',
    );
    expect(
      tester.widget<TextField>(find.byType(TextField).at(1)).controller!.text,
      '4.5',
    );
    // supplier dropdown lists active suppliers
    await tester.tap(find.text('Supplier'));
    await tester.pumpAndSettle();
    expect(find.text('Acme Supplies'), findsOneWidget);
    await tester.tap(find.text('Cafe Latte'));
    await tester.pumpAndSettle();
    expect(find.text('Generate POs'), findsOneWidget);
  });

  testWidgets('batch generate posts edited rows and shows result', (
    tester,
  ) async {
    final purchasing = _FakePurchasing();
    final container = _container(purchasing: purchasing);
    addTearDown(container.dispose);
    await _pump(tester, container);

    await tester.tap(find.text('Replenishment'));
    await tester.pumpAndSettle();

    // edit quantity and pick an explicit supplier override
    await tester.enterText(find.byType(TextField).first, '5');
    await tester.pump();
    await tester.tap(find.text('Supplier'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Acme Supplies'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Generate POs'));
    await tester.pumpAndSettle();

    expect(purchasing.lastItems, [
      {
        'product_id': 3,
        'quantity_ordered': 5,
        'unit_cost': 4.5,
        'supplier_id': 7,
      },
    ]);
    expect(find.text('1 draft purchase order(s) created'), findsOneWidget);
    expect(find.textContaining('Cafe Latte'), findsOneWidget);
    expect(find.textContaining('#4: no supplier history'), findsOneWidget);

    await tester.tap(find.text('OK'));
    await tester.pumpAndSettle();
    // dialog closed, list reloaded
    expect(find.text('1 draft purchase order(s) created'), findsNothing);
  });
}
