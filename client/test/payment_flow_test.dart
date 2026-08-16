import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/api_client.dart';
import 'package:octopos_client/core/api_repositories.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/core/token_store.dart';
import 'package:octopos_client/features/pos/cart_controller.dart';
import 'package:octopos_client/features/pos/checkout_sheet.dart';

void main() {
  group('PaymentLine.fromJson', () {
    test('parses the backend /payments response shape', () {
      final payment = PaymentLine.fromJson(const {
        'id': 41,
        'order_id': 7,
        'user_id': 3,
        'payment_method': 'cash',
        'amount': 20.0,
        'idempotency_key': 'smoke-pay-001',
        'created_at': '2026-08-16T12:00:00',
      });
      expect(payment.id, 41);
      expect(payment.orderId, 7);
      expect(payment.paymentMethod, 'cash');
      expect(payment.amount, 20.0);
    });

    test('missing idempotency_key and user_id are tolerated', () {
      final payment = PaymentLine.fromJson(const {
        'id': 1,
        'order_id': 1,
        'payment_method': 'card',
        'amount': 5.0,
      });
      expect(payment.paymentMethod, 'card');
      expect(payment.userId, 0);
    });
  });

  group('CheckoutSheet payment flow', () {
    testWidgets(
      'paying pops the created order (regression: Payment parsed as Order)',
      (tester) async {
        final container = ProviderContainer(
          overrides: [
            localizationControllerProvider.overrideWith(
              _FixedLanguageLocalization.new,
            ),
            orderRepositoryProvider.overrideWithValue(_FakeOrders()),
          ],
        );
        addTearDown(container.dispose);

        // Seed the cart with one line so subtotal > 0.
        final cart = container.read(cartControllerProvider.notifier);
        cart.addProduct(
          const Product(
            id: 1,
            name: 'Latte',
            sku: 'LATTE-1',
            price: 4.50,
            stockQuantity: 10,
            minStock: 0,
            reorderPoint: 0,
            leadTimeDays: 0,
          ),
        );

        Order? popped;
        await tester.pumpWidget(
          UncontrolledProviderScope(
            container: container,
            child: MaterialApp(
              home: Scaffold(
                body: Builder(
                  builder: (context) => Center(
                    child: ElevatedButton(
                      onPressed: () async {
                        final result = await showModalBottomSheet<Order>(
                          context: context,
                          isScrollControlled: true,
                          builder: (_) => const CheckoutSheet(),
                        );
                        popped = result;
                      },
                      child: const Text('open'),
                    ),
                  ),
                ),
              ),
            ),
          ),
        );
        await tester.tap(find.text('open'));
        await tester.pumpAndSettle();

        // Card payment (no cash amount needed).
        await tester.tap(find.text('Card'));
        await tester.pumpAndSettle();
        await tester.tap(find.text('Pay'));
        await tester.pumpAndSettle();

        expect(
          popped,
          isNotNull,
          reason: 'checkout must pop the settled order',
        );
        expect(popped!.id, 100);
      },
    );

    testWidgets('split payment settles cash + card portions', (tester) async {
      final container = ProviderContainer(
        overrides: [
          localizationControllerProvider.overrideWith(
            _FixedLanguageLocalization.new,
          ),
          orderRepositoryProvider.overrideWithValue(_FakeOrders()),
        ],
      );
      addTearDown(container.dispose);

      final cart = container.read(cartControllerProvider.notifier);
      cart.addProduct(
        const Product(
          id: 1,
          name: 'Latte',
          sku: 'LATTE-1',
          price: 4.50,
          stockQuantity: 10,
          minStock: 0,
          reorderPoint: 0,
          leadTimeDays: 0,
        ),
      );

      Order? popped;
      await tester.pumpWidget(
        UncontrolledProviderScope(
          container: container,
          child: MaterialApp(
            home: Scaffold(
              body: Builder(
                builder: (context) => Center(
                  child: ElevatedButton(
                    onPressed: () async {
                      final result = await showModalBottomSheet<Order>(
                        context: context,
                        isScrollControlled: true,
                        builder: (_) => const CheckoutSheet(),
                      );
                      popped = result;
                    },
                    child: const Text('open'),
                  ),
                ),
              ),
            ),
          ),
        ),
      );
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();

      await tester.tap(find.text('Split'));
      await tester.pumpAndSettle();
      await tester.enterText(
        find.widgetWithText(TextField, 'Cash portion'),
        '2.00',
      );
      await tester.tap(find.text('Pay'));
      await tester.pumpAndSettle();

      expect(popped, isNotNull, reason: 'split checkout must pop the order');
      expect(popped!.id, 100);
    });
  });
}

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

class _FakeOrders extends OrderRepository {
  _FakeOrders()
    : super(ApiClient(store: TokenStore(), onSessionExpired: () {}));

  @override
  Future<Order> createOrder({
    required List<Map<String, dynamic>> items,
    int? customerId,
    String? promotionCode,
    int redeemPoints = 0,
    String? idempotencyKey,
  }) async {
    return const Order(
      id: 100,
      userId: 1,
      subtotalAmount: 4.5,
      discountAmount: 0,
      taxableBaseAmount: 4.5,
      taxTotalAmount: 0,
      grandTotalAmount: 4.5,
      totalAmount: 4.5,
      paidAmount: 4.5,
      changeAmount: 0,
      remainingAmount: 0,
      redeemedPoints: 0,
      status: 'pending',
      reservationStatus: '',
    );
  }

  @override
  Future<Order> addSplitPayments({
    required int orderId,
    required List<Map<String, String>> payments,
  }) async {
    return const Order(
      id: 100,
      userId: 1,
      subtotalAmount: 4.5,
      discountAmount: 0,
      taxableBaseAmount: 4.5,
      taxTotalAmount: 0,
      grandTotalAmount: 4.5,
      totalAmount: 4.5,
      paidAmount: 4.5,
      changeAmount: 0,
      remainingAmount: 0,
      redeemedPoints: 0,
      status: 'pending',
      reservationStatus: '',
    );
  }

  @override
  Future<PaymentLine> addPayment({
    required int orderId,
    required String method,
    required int amountCents,
    String? idempotencyKey,
  }) async {
    return PaymentLine(
      id: 1,
      orderId: orderId,
      paymentMethod: method,
      amount: amountCents / 100,
      userId: 1,
    );
  }
}
