import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/api_client.dart';
import 'package:octopos_client/core/api_repositories.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/core/token_store.dart';
import 'package:octopos_client/features/orders/orders_screen.dart';

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

  @override
  Future<List<Order>> recentOrders({int limit = 50}) async => stored;

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

ProviderContainer _container() => ProviderContainer(
  overrides: [
    localizationControllerProvider.overrideWith(_FixedLanguageLocalization.new),
    orderRepositoryProvider.overrideWithValue(_FakeOrders()),
  ],
);

Future<void> _pump(WidgetTester tester, ProviderContainer container) async {
  await tester.pumpWidget(
    UncontrolledProviderScope(
      container: container,
      child: const MaterialApp(home: OrdersScreen()),
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
    expect(
      find.descendant(
        of: find.byType(ListTile),
        matching: find.text('Completed'),
      ),
      findsOneWidget,
    );
    expect(
      find.descendant(
        of: find.byType(ListTile),
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
    await tester.pumpAndSettle();

    final fake = container.read(orderRepositoryProvider) as _FakeOrders;
    expect(fake.cancelCount, 1);
    expect(fake.stored.firstWhere((o) => o.id == 2).status, 'cancelled');
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
}
