import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/api_client.dart';
import 'package:octopos_client/core/api_repositories.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/core/token_store.dart';
import 'package:octopos_client/features/serving/serving_screen.dart';

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

Order _order(int id, String servingStatus, {String status = 'completed'}) =>
    Order(
      id: id,
      userId: 1,
      subtotalAmount: 10,
      discountAmount: 0,
      taxableBaseAmount: 10,
      taxTotalAmount: 0,
      grandTotalAmount: 10,
      totalAmount: 10,
      paidAmount: 10,
      changeAmount: 0,
      remainingAmount: 0,
      redeemedPoints: 0,
      status: status,
      servingStatus: servingStatus,
      reservationStatus: 'committed',
      createdAt: '2026-08-17T10:00:00',
      items: const [
        OrderItem(
          id: 1,
          orderId: 1,
          productId: 1,
          quantity: 2,
          unitPrice: 5,
          product: Product(
            id: 1,
            name: 'Latte',
            sku: 'SKU-1',
            price: 5.0,
            stockQuantity: 10,
            minStock: 0,
            reorderPoint: 0,
            leadTimeDays: 0,
          ),
        ),
      ],
    );

class _FakeServing extends OrderRepository {
  _FakeServing()
    : super(ApiClient(store: TokenStore(), onSessionExpired: () {}));

  List<Order> stored = [
    _order(1, 'queued'),
    _order(2, 'preparing'),
    _order(3, 'ready'),
  ];
  int transitions = 0;

  @override
  Future<List<Order>> servingQueue({String? status}) async => stored;

  @override
  Future<Order> startServing(int orderId) async {
    transitions++;
    stored = [
      for (final o in stored)
        o.id == orderId ? _order(orderId, 'preparing') : o,
    ];
    return stored.first;
  }

  @override
  Future<Order> markReady(int orderId) async {
    transitions++;
    stored = [for (final o in stored) o.id == orderId ? _order(orderId, 'ready') : o];
    return stored.first;
  }

  @override
  Future<Order> markServed(int orderId) async {
    transitions++;
    stored = [for (final o in stored) o.id != orderId ? o : _order(orderId, 'served')];
    return stored.first;
  }

  @override
  Stream<Map<String, dynamic>> servingEvents() =>
      const Stream.empty(); // force polling path
}

Widget _app(ProviderContainer container) => UncontrolledProviderScope(
  container: container,
  child: const MaterialApp(home: Scaffold(body: ServingScreen())),
);

ProviderContainer _container({required OrderRepository repo}) {
  final container = ProviderContainer(
    overrides: [
      orderRepositoryProvider.overrideWithValue(repo),
      localizationControllerProvider.overrideWith(
        _FixedLanguageLocalization.new,
      ),
    ],
  );
  return container;
}

/// Disposes the tree and container inside the test body so pending
/// poll timers are cancelled before the binding's invariant checks.
Future<void> _dispose(WidgetTester tester, ProviderContainer container) async {
  await tester.pumpWidget(const SizedBox());
  container.dispose();
}

void main() {
  testWidgets('renders queue cards with per-status action buttons', (tester) async {
    final container = _container(repo: _FakeServing());
    await tester.pumpWidget(_app(container));
    await tester.pumpAndSettle();

    expect(find.text('Order #1'), findsOneWidget);
    expect(find.text('Order #2'), findsOneWidget);
    expect(find.text('Order #3'), findsOneWidget);
    expect(find.text('2× Latte'), findsNWidgets(3));

    expect(find.text('Queued'), findsOneWidget);
    expect(find.text('Preparing'), findsOneWidget);
    expect(find.text('Ready'), findsOneWidget);

    expect(find.text('Start preparing'), findsOneWidget);
    expect(find.text('Mark ready'), findsOneWidget);
    expect(find.text('Mark served'), findsOneWidget);

    await _dispose(tester, container);
  });

  testWidgets('advancing status updates the queue and buttons', (tester) async {
    final fake = _FakeServing();
    final container = _container(repo: fake);
    await tester.pumpWidget(_app(container));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Start preparing'));
    await tester.pumpAndSettle();

    expect(fake.transitions, 1);
    // Order #1 is now preparing: its Ready button appears, Start disappears.
    expect(find.text('Mark ready'), findsNWidgets(2));
    expect(find.text('Start preparing'), findsNothing);

    await tester.tap(find.text('Mark served'));
    await tester.pumpAndSettle();
    expect(fake.transitions, 2);

    await _dispose(tester, container);
  });

  testWidgets('empty queue shows empty state', (tester) async {
    final fake = _FakeServing()..stored = [];
    final container = _container(repo: fake);
    await tester.pumpWidget(_app(container));
    await tester.pumpAndSettle();

    expect(find.text('No orders waiting to be served'), findsOneWidget);

    await _dispose(tester, container);
  });
}