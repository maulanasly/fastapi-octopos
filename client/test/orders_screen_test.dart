import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:octopos_client/core/api_client.dart';
import 'package:octopos_client/core/api_repositories.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/core/pagination.dart';
import 'package:octopos_client/core/skeletons.dart';
import 'package:octopos_client/core/token_store.dart';
import 'package:octopos_client/features/orders/orders_screen.dart';
import 'package:octopos_client/features/pos/receipt_screen.dart';

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

Order _order(int id, String status, {double total = 10.0}) => Order(
  id: id,
  userId: 1,
  subtotalAmount: total,
  discountAmount: 0,
  taxableBaseAmount: total,
  taxTotalAmount: 0,
  grandTotalAmount: total,
  totalAmount: total,
  paidAmount: status == 'completed' ? total : 0,
  changeAmount: 0,
  remainingAmount: status == 'completed' ? 0 : total,
  redeemedPoints: 0,
  status: status,
  reservationStatus: '',
  createdAt: '2026-08-16T10:00:00',
  items: const [
    OrderItem(id: 1, orderId: 1, productId: 1, quantity: 1, unitPrice: 10),
  ],
);

class _FakeOrders extends OrderRepository {
  _FakeOrders()
    : super(ApiClient(store: TokenStore(), onSessionExpired: () {}));

  List<Order> stored = [_order(1, 'completed'), _order(2, 'pending')];
  int cancelCount = 0;
  bool failAll = false;
  Completer<void>? gate;

  @override
  Future<List<Order>> recentOrders({
    PaginationParams pagination = PaginationParams.recentOrders,
    String? status,
  }) async {
    if (failAll) throw Exception('boom');
    if (gate != null) await gate!.future;
    var rows = stored;
    if (status != null) {
      rows = rows.where((o) => o.status == status).toList();
    }
    return rows.skip(pagination.offset).take(pagination.limit).toList();
  }

  @override
  Future<Order> cancel(int orderId) async {
    cancelCount++;
    stored = stored.map((o) {
      if (o.id == orderId) {
        return _order(orderId, 'cancelled');
      }
      return o;
    }).toList();
    return _order(orderId, 'cancelled');
  }

  @override
  Future<OrderReceipt> receipt(int orderId) async => OrderReceipt(
    orderId: orderId,
    subtotalAmount: 10,
    discountAmount: 0,
    redeemedPoints: 0,
    taxableBaseAmount: 10,
    taxTotalAmount: 0,
    grandTotalAmount: 10,
    totalAmount: 10,
    paidAmount: 10,
    changeAmount: 0,
    remainingAmount: 0,
    status: 'completed',
    reservationStatus: '',
  );
}

ProviderContainer _container({_FakeOrders? orders}) => ProviderContainer(
  overrides: [
    localizationControllerProvider.overrideWith(_FixedLanguageLocalization.new),
    orderRepositoryProvider.overrideWithValue(orders ?? _FakeOrders()),
  ],
);

Future<void> _pump(WidgetTester tester, ProviderContainer container) async {
  // Minimal GoRouter mirror of the production routes under test:
  // reprint uses context.push('/receipt/:orderId'), which requires a
  // GoRouter in scope (a bare MaterialApp would throw).
  final router = GoRouter(
    initialLocation: '/orders',
    routes: [
      GoRoute(
        path: '/orders',
        builder: (context, state) => const OrdersScreen(),
      ),
      GoRoute(
        path: '/receipt/:orderId',
        builder: (context, state) => ReceiptScreen(
          orderId: int.parse(state.pathParameters['orderId']!),
        ),
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
}

void main() {
  testWidgets('lists orders with status and total', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pump(tester, container);

    expect(find.text('Order #1'), findsOneWidget);
    expect(find.text('Order #2'), findsOneWidget);
    // Status pills render once per order in the OctoTable (wide) or
    // ListTile cards (narrow). Scope to Chip (not the ChoiceChip
    // filters, which share the same labels).
    expect(
      find.descendant(
        of: find.byType(Chip),
        matching: find.text('Completed'),
      ),
      findsOneWidget,
    );
    expect(
      find.descendant(
        of: find.byType(Chip),
        matching: find.text('Pending'),
      ),
      findsOneWidget,
    );
    expect(find.textContaining(r'$10.00'), findsNWidgets(2));
  });

  testWidgets('status filter narrows the list', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pump(tester, container);

    await tester.tap(find.byKey(const Key('filter-pending')));
    await tester.pumpAndSettle();

    expect(find.text('Order #2'), findsOneWidget);
    expect(find.text('Order #1'), findsNothing);
  });

  testWidgets('cancel confirms and refreshes', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pump(tester, container);

    await tester.tap(find.byIcon(Icons.cancel_outlined));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Cancel order').last);
    // Let the dialog dismiss, the cancel land, and the SnackBar present
    // — but don't settle past the SnackBar's 4s auto-dismiss.
    await tester.pump();
    await tester.pump();
    await tester.pump(const Duration(seconds: 1));

    final fake = container.read(orderRepositoryProvider) as _FakeOrders;
    expect(fake.cancelCount, 1);
    expect(fake.stored.firstWhere((o) => o.id == 2).status, 'cancelled');
    expect(find.text('Order #2 cancelled'), findsOneWidget);
  });

  testWidgets('reprint opens the receipt', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pump(tester, container);

    await tester.tap(find.byIcon(Icons.receipt_long).first);
    await tester.pumpAndSettle();

    expect(
      find.textContaining('Done'),
      findsOneWidget,
      reason: 'receipt screen shown',
    );
    expect(find.textContaining('Order #1'), findsWidgets);
  });

  testWidgets('load more appends the next page', (tester) async {
    final fake = _FakeOrders()
      ..stored = [
        for (var i = 1; i <= 55; i++) _order(i, 'pending'),
        _order(100, 'completed'),
      ];
    final container = _container(orders: fake);
    addTearDown(container.dispose);
    await _pump(tester, container);

    expect(find.text('Order #50'), findsOneWidget);
    expect(find.text('Order #51'), findsNothing);
    expect(find.text('Load more (50 shown)'), findsOneWidget);

    await tester.ensureVisible(find.text('Load more (50 shown)'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Load more (50 shown)'));
    await tester.pumpAndSettle();

    expect(find.text('Order #51'), findsOneWidget);
    expect(find.text('Order #55'), findsOneWidget);
    expect(find.textContaining('Load more'), findsNothing);
  });

  testWidgets('failed load shows an error with retry', (tester) async {
    final fake = _FakeOrders()..failAll = true;
    final container = _container(orders: fake);
    addTearDown(container.dispose);
    await _pump(tester, container);

    expect(
      find.text('Something went wrong. Please try again.'),
      findsOneWidget,
    );

    fake.failAll = false;
    await tester.tap(find.text('Retry'));
    await tester.pumpAndSettle();

    expect(find.text('Order #1'), findsOneWidget);
    expect(find.text('Order #2'), findsOneWidget);
  });

  testWidgets('loading shows a skeleton, not a bare spinner', (tester) async {
    final fake = _FakeOrders()..gate = Completer<void>();
    final container = _container(orders: fake);
    addTearDown(container.dispose);
    // No settle: the shimmer ticker schedules frames indefinitely
    // while the gated load is pending.
    final router = GoRouter(
      initialLocation: '/orders',
      routes: [
        GoRoute(
          path: '/orders',
          builder: (context, state) => const OrdersScreen(),
        ),
        GoRoute(
          path: '/receipt/:orderId',
          builder: (context, state) => ReceiptScreen(
            orderId: int.parse(state.pathParameters['orderId']!),
          ),
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
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.byType(OrderRowSkeleton), findsOneWidget);

    fake.gate!.complete();
    await tester.pumpAndSettle();

    expect(find.byType(OrderRowSkeleton), findsNothing);
    expect(find.text('Order #1'), findsOneWidget);
  });
}
