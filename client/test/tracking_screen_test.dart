import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/api_client.dart';
import 'package:octopos_client/core/api_repositories.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/core/token_store.dart';
import 'package:octopos_client/features/tracking/tracking_screen.dart';
import 'package:octopos_client/features/tracking/trip_map_screen.dart';

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

class _FakeTracking extends OrderRepository {
  _FakeTracking()
    : super(ApiClient(store: TokenStore(), onSessionExpired: () {}));

  List<TrackedOrder> stored = [
    const TrackedOrder(
      orderId: 7,
      status: 'completed',
      trackingStatus: 'en_route',
      destinationAddress: '123 Main St',
      destinationLat: -6.2,
      destinationLng: 106.8,
      latestLocation: LocationUpdate(lat: -6.21, lng: 106.81),
      createdAt: '2026-08-17T10:00:00',
    ),
  ];
  int transitions = 0;

  @override
  Future<List<TrackedOrder>> activeTracking() async => stored;

  @override
  Future<Order> trackingStatus({
    required int orderId,
    required String status,
  }) async {
    transitions++;
    stored = [
      for (final t in stored)
        t.orderId == orderId
            ? TrackedOrder(
                orderId: t.orderId,
                status: t.status,
                trackingStatus: status,
                destinationAddress: t.destinationAddress,
                destinationLat: t.destinationLat,
                destinationLng: t.destinationLng,
                latestLocation: t.latestLocation,
                createdAt: t.createdAt,
              )
            : t,
    ];
    return Order(
      id: orderId,
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
      trackingStatus: status,
      reservationStatus: 'committed',
    );
  }

  @override
  Future<Map<String, dynamic>> reportLocation({
    required int orderId,
    required double lat,
    required double lng,
    String source = 'gps',
  }) async {
    stored = [
      for (final t in stored)
        t.orderId == orderId
            ? TrackedOrder(
                orderId: t.orderId,
                status: t.status,
                trackingStatus: t.trackingStatus,
                destinationAddress: t.destinationAddress,
                destinationLat: t.destinationLat,
                destinationLng: t.destinationLng,
                latestLocation: LocationUpdate(lat: lat, lng: lng),
                createdAt: t.createdAt,
              )
            : t,
    ];
    return {};
  }

  @override
  Stream<Map<String, dynamic>> servingEvents() =>
      const Stream.empty(); // force polling path
}

Widget _app(ProviderContainer container) => UncontrolledProviderScope(
  container: container,
  child: const MaterialApp(home: Scaffold(body: TrackingScreen())),
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

Future<void> _dispose(WidgetTester tester, ProviderContainer container) async {
  await tester.pumpWidget(const SizedBox());
  container.dispose();
}

void main() {
  testWidgets('renders tracked trips with status and destination',
      (tester) async {
    final container = _container(repo: _FakeTracking());
    await tester.pumpWidget(_app(container));
    await tester.pumpAndSettle();

    expect(find.text('Order #7 · En route'), findsOneWidget);
    expect(find.text('123 Main St'), findsOneWidget);
    expect(find.byIcon(Icons.directions_car_outlined), findsOneWidget);
    await _dispose(tester, container);
  });

  testWidgets('shows empty state when no trips', (tester) async {
    final repo = _FakeTracking()..stored = [];
    final container = _container(repo: repo);
    await tester.pumpWidget(_app(container));
    await tester.pumpAndSettle();

    expect(find.text('No active trips being tracked'), findsOneWidget);
    await _dispose(tester, container);
  });

  testWidgets('trip map shows stepper and advances en_route -> on_site',
      (tester) async {
    final repo = _FakeTracking();
    final container = _container(repo: repo);
    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: MaterialApp(
          home: TripMapScreen(trip: repo.stored.first),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Order #7'), findsOneWidget);
    expect(find.text('En route'), findsOneWidget);
    expect(find.text('I\'m on site'), findsOneWidget);

    await tester.tap(find.text('I\'m on site'));
    await tester.pumpAndSettle();

    expect(repo.transitions, 1);
    expect(repo.stored.first.trackingStatus, 'on_site');
    await _dispose(tester, container);
  });
}
