import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/api_client.dart';
import 'package:octopos_client/core/api_repositories.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/core/token_store.dart';
import 'package:octopos_client/features/reports/reports_screen.dart';

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

class _FakeReports extends ReportRepository {
  _FakeReports()
    : super(ApiClient(store: TokenStore(), onSessionExpired: () {}));

  @override
  Future<SalesSummary> sales({String? startDate, String? endDate}) async =>
      const SalesSummary(
        grossRevenue: 100,
        totalDiscounts: 5,
        totalRevenue: 95,
        totalRefunds: 2,
        netRevenue: 93,
        orderCount: 4,
        averageOrderValue: 23.75,
      );

  @override
  Future<List<TopProductItem>> topProducts({
    String? startDate,
    String? endDate,
    int limit = 10,
  }) async => const [
    TopProductItem(
      productId: 1,
      productName: 'Cafe Latte',
      productSku: 'LATTE',
      totalQuantitySold: 12,
      totalRevenue: 60,
    ),
  ];

  @override
  Future<List<CategorySalesItem>> categorySales({
    String? startDate,
    String? endDate,
  }) async => const [
    CategorySalesItem(
      categoryId: 1,
      categoryName: 'Beverages',
      totalRevenue: 60,
      totalQuantitySold: 12,
    ),
  ];

  @override
  Future<List<Product>> lowStock() async => const [];

  @override
  Future<DailyCloseTotals> dailyClose() async => const DailyCloseTotals(
    grossSalesTotal: 120,
    netSalesTotal: 110,
    cashSalesTotal: 80,
    nonCashSalesTotal: 30,
    refundsTotal: 10,
    cashVariance: 0,
    nonCashVariance: 0,
    completedOrderCount: 6,
    shiftCount: 2,
  );

  @override
  Future<List<DailyShiftItem>> shifts() async => const [
    DailyShiftItem(
      reconciliationId: 7,
      drawerSessionId: 3,
      closedAt: '2026-08-16T10:00:00',
      operatorName: 'Budi Cashier',
      cashSalesTotal: 60,
      nonCashSalesTotal: 20,
      refundsTotal: 5,
      grossSalesTotal: 80,
      netSalesTotal: 75,
      completedOrderCount: 4,
      cashVariance: 2,
    ),
  ];

  @override
  Future<ShiftReport> shiftReport(int reconciliationId) async =>
      const ShiftReport(
        reconciliationId: 7,
        drawerSessionId: 3,
        closedAt: '2026-08-16T10:00:00',
        operatorName: 'Budi Cashier',
        startingCash: 50,
        expectedCash: 108,
        countedCash: 110,
        cashVariance: 2,
        cashSalesTotal: 60,
        nonCashSalesTotal: 20,
        refundsTotal: 5,
        grossSalesTotal: 80,
        netSalesTotal: 75,
        completedOrderCount: 4,
      );
}

ProviderContainer _container() => ProviderContainer(
  overrides: [
    localizationControllerProvider.overrideWith(_FixedLanguageLocalization.new),
    reportRepositoryProvider.overrideWithValue(_FakeReports()),
  ],
);

Future<void> _pump(WidgetTester tester, ProviderContainer container) async {
  await tester.pumpWidget(
    UncontrolledProviderScope(
      container: container,
      child: const MaterialApp(home: ReportsScreen()),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('shows daily close totals and shift list', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pump(tester, container);

    await tester.scrollUntilVisible(
      find.text('Today close'),
      200,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Today close'), findsOneWidget);
    expect(find.textContaining(r'$120.00'), findsWidgets);

    await tester.scrollUntilVisible(
      find.text('Shifts #7 — Budi Cashier'),
      200,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Shifts #7 — Budi Cashier'), findsOneWidget);
    expect(find.textContaining(r'$75.00'), findsWidgets);
  });

  testWidgets('tapping a shift opens its report', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pump(tester, container);

    await tester.scrollUntilVisible(
      find.text('Shifts #7 — Budi Cashier'),
      200,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.tap(find.text('Shifts #7 — Budi Cashier'));
    await tester.pumpAndSettle();

    expect(find.text('Shifts #7'), findsOneWidget);
    expect(find.textContaining('Cashier: Budi Cashier'), findsOneWidget);
    expect(find.textContaining(r'$2.00'), findsWidgets); // variance
  });
}
