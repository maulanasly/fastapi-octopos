/// Receipt close behavior: pushed flows pop to their opener; a
/// cold-started deep link returns to a safe recorded origin, else POS.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:octopos_client/core/api_client.dart';
import 'package:octopos_client/core/api_repositories.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/core/pagination.dart';
import 'package:octopos_client/core/token_store.dart';
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

class _FailingOrders extends OrderRepository {
  _FailingOrders()
    : super(ApiClient(store: TokenStore(), onSessionExpired: () {}));

  @override
  Future<List<Order>> recentOrders({
    PaginationParams pagination = PaginationParams.recentOrders,
    String? status,
  }) async => const [];

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

Future<void> _pumpColdLink(
  WidgetTester tester,
  ProviderContainer container,
  String location,
) async {
  final router = GoRouter(
    initialLocation: location,
    routes: [
      GoRoute(
        path: '/receipt/:orderId',
        builder: (context, state) => ReceiptScreen(
          orderId: int.parse(state.pathParameters['orderId']!),
          from: state.uri.queryParameters['from'],
        ),
      ),
      GoRoute(
        path: '/orders',
        builder: (context, state) => const Text('orders stub'),
      ),
      GoRoute(
        path: '/pos',
        builder: (context, state) => const Text('pos stub'),
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

ProviderContainer _container() => ProviderContainer(
  overrides: [
    localizationControllerProvider.overrideWith(_FixedLanguageLocalization.new),
    orderRepositoryProvider.overrideWithValue(_FailingOrders()),
  ],
);

void main() {
  testWidgets('cold link Done returns to the recorded origin', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pumpColdLink(tester, container, '/receipt/1?from=/orders');

    await tester.tap(find.text('Done'));
    await tester.pumpAndSettle();

    expect(find.text('orders stub'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('cold link Done falls back to POS without an origin', (
    tester,
  ) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pumpColdLink(tester, container, '/receipt/1');

    await tester.tap(find.text('Done'));
    await tester.pumpAndSettle();

    expect(find.text('pos stub'), findsOneWidget);
  });

  testWidgets('cold link Done rejects an unsafe origin', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pumpColdLink(tester, container, '/receipt/1?from=https://evil');

    await tester.tap(find.text('Done'));
    await tester.pumpAndSettle();

    expect(find.text('pos stub'), findsOneWidget);
  });
}
