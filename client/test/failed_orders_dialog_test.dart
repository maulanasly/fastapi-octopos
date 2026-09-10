/// Failed-orders dialog: failed rows render with mapped errors, retry
/// re-syncs them away, discard drops them.
library;

import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/api_client.dart';
import 'package:octopos_client/core/api_repositories.dart';
import 'package:octopos_client/core/db/app_database.dart';
import 'package:octopos_client/core/db/database_provider.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/core/sync/outbox_repository.dart';
import 'package:octopos_client/core/token_store.dart';
import 'package:octopos_client/features/pos/failed_orders_dialog.dart';

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

Order _syncedOrder() => Order(
  id: 55,
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
  items: const [],
);

class _FakeOrders extends OrderRepository {
  _FakeOrders()
    : super(ApiClient(store: TokenStore(), onSessionExpired: () {}));

  int creates = 0;

  @override
  Future<Order> createOrder({
    required List<Map<String, dynamic>> items,
    int? customerId,
    String? promotionCode,
    int redeemPoints = 0,
    String? idempotencyKey,
    String? destinationAddress,
    double? destinationLat,
    double? destinationLng,
  }) async {
    creates++;
    return _syncedOrder();
  }
}

void main() {
  testWidgets('retry syncs a failed row away, discard drops it', (
    tester,
  ) async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final fakeOrders = _FakeOrders();
    final container = ProviderContainer(
      overrides: [
        localizationControllerProvider.overrideWith(
          _FixedLanguageLocalization.new,
        ),
        appDatabaseProvider.overrideWithValue(db),
        orderRepositoryProvider.overrideWithValue(fakeOrders),
      ],
    );
    addTearDown(container.dispose);

    final outbox = container.read(outboxRepositoryProvider);
    final first = await outbox.enqueueOrder(
      items: const [
        {'product_id': 1, 'quantity': 1},
      ],
    );
    await outbox.markFailed(first, 'http_422');
    final second = await outbox.enqueueOrder(
      items: const [
        {'product_id': 2, 'quantity': 1},
      ],
    );
    await outbox.markFailed(second, 'unexpected_error');

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: const MaterialApp(home: Scaffold(body: FailedOrdersDialog())),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Failed orders'), findsOneWidget);
    expect(find.text('Order #$first'), findsOneWidget);
    expect(
      find.text('Please check the entered values.'),
      findsOneWidget,
    );
    expect(find.text('Something went wrong. Please try again.'), findsOneWidget);

    // Retry re-queues and immediately syncs: the row is removed.
    await tester.tap(find.byIcon(Icons.refresh).first);
    await tester.pumpAndSettle();

    expect(fakeOrders.creates, 1);
    expect(find.text('Order #$first'), findsNothing);
    expect(find.text('Order #$second'), findsOneWidget);

    // Discard drops the remaining row without syncing.
    await tester.tap(find.byIcon(Icons.delete_outline));
    await tester.pumpAndSettle();

    expect(fakeOrders.creates, 1);
    expect(find.text('No failed orders'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
