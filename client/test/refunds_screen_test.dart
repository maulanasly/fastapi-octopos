/// Refunds regression: the order list refreshes after a refund (the
/// reload must run inside setState), failures render a localized
/// message instead of the raw exception, and the list error view uses
/// the backend-aware message.
library;

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/api_client.dart';
import 'package:octopos_client/core/api_repositories.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/core/pagination.dart';
import 'package:octopos_client/core/skeletons.dart';
import 'package:octopos_client/core/token_store.dart';
import 'package:octopos_client/features/refunds/refund_screen.dart';

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

Order _order(int id) => Order(
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
  status: 'completed',
  reservationStatus: '',
  createdAt: '2026-08-16T10:00:00',
  items: const [
    OrderItem(id: 7, orderId: 1, productId: 1, quantity: 2, unitPrice: 5),
  ],
);

class _FakeRefunds extends OrderRepository {
  _FakeRefunds({this.failSubmit = false})
    : super(ApiClient(store: TokenStore(), onSessionExpired: () {}));

  final bool failSubmit;
  List<Order> stored = [_order(1)];
  int submits = 0;
  Completer<void>? gate;

  @override
  Future<List<Order>> recentOrders({
    PaginationParams pagination = PaginationParams.recentOrders,
    String? status,
  }) async {
    if (gate != null) await gate!.future;
    var rows = stored;
    if (status != null) {
      rows = rows.where((o) => o.status == status).toList();
    }
    return rows.skip(pagination.offset).take(pagination.limit).toList();
  }

  @override
  Future<Refund> createRefund({
    required int orderId,
    required List<Map<String, dynamic>> items,
    String? reason,
    String? paymentMethod,
    String? idempotencyKey,
  }) async {
    submits++;
    if (failSubmit) throw Exception('boom');
    stored = const [];
    return Refund(id: 9, orderId: orderId, userId: 1, totalAmount: 10);
  }
}

ProviderContainer _container(_FakeRefunds fake) => ProviderContainer(
  overrides: [
    localizationControllerProvider.overrideWith(
      _FixedLanguageLocalization.new,
    ),
    orderRepositoryProvider.overrideWithValue(fake),
  ],
);

Future<void> _pump(WidgetTester tester, ProviderContainer container) async {
  await tester.pumpWidget(
    UncontrolledProviderScope(
      container: container,
      child: const MaterialApp(home: RefundScreen()),
    ),
  );
  await tester.pumpAndSettle();
}

/// Select the first order and one unit of its first item.
Future<void> _selectOneUnit(WidgetTester tester) async {
  await tester.tap(find.text('Order #1'));
  await tester.pumpAndSettle();
  // Stepper: minus, count, plus — tap the plus.
  await tester.tap(find.byIcon(Icons.add_circle_outline));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('successful refund clears the selection and reloads', (
    tester,
  ) async {
    final fake = _FakeRefunds();
    final container = _container(fake);
    addTearDown(container.dispose);
    await _pump(tester, container);

    await _selectOneUnit(tester);
    expect(find.byTooltip('Decrease quantity'), findsOneWidget);
    expect(find.byTooltip('Increase quantity'), findsOneWidget);
    await tester.tap(find.text('Refund selected items'));
    await tester.pumpAndSettle();

    expect(fake.submits, 1);
    expect(tester.takeException(), isNull);
    expect(find.text('Refund created successfully'), findsOneWidget);
    // Picker reloaded: the refunded order is gone, empty state shows.
    expect(find.text('Order #1'), findsNothing);
  });

  testWidgets('failed refund shows a localized message, not the exception', (
    tester,
  ) async {
    final fake = _FakeRefunds(failSubmit: true);
    final container = _container(fake);
    addTearDown(container.dispose);
    await _pump(tester, container);

    await _selectOneUnit(tester);
    await tester.tap(find.text('Refund selected items'));
    await tester.pumpAndSettle();

    expect(fake.submits, 1);
    expect(tester.takeException(), isNull);
    expect(
      find.text('Something went wrong. Please try again.'),
      findsOneWidget,
    );
    expect(find.textContaining('boom'), findsNothing);
    expect(find.textContaining('Exception'), findsNothing);
  });

  testWidgets('loading shows a skeleton, not a bare spinner', (tester) async {
    final fake = _FakeRefunds()..gate = Completer<void>();
    final container = _container(fake);
    addTearDown(container.dispose);
    // No settle: the shimmer ticker schedules frames indefinitely
    // while the gated load is pending.
    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: const MaterialApp(home: RefundScreen()),
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
