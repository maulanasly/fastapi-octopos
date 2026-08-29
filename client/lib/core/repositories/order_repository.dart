library;

import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api_client.dart';
import '../models.dart';
import 'helpers.dart';

final orderRepositoryProvider = Provider<OrderRepository>(
  (ref) => OrderRepository(ref.watch(apiClientProvider)),
);

/// One shared SSE connection for every consumer (serving queue + tracking
/// map previously each opened their own stream to the same endpoint).
/// The upstream connects while at least one listener is subscribed and
/// disconnects when the last one leaves.
final servingEventBusProvider = Provider<Stream<Map<String, dynamic>>>((ref) {
  final repo = ref.watch(orderRepositoryProvider);
  late final StreamController<Map<String, dynamic>> controller;
  StreamSubscription<Map<String, dynamic>>? upstream;
  var listeners = 0;
  controller = StreamController<Map<String, dynamic>>.broadcast(
    onListen: () {
      listeners++;
      upstream ??= repo.servingEvents().listen(
        controller.add,
        onError: controller.addError,
        onDone: () => upstream = null,
        cancelOnError: false,
      );
    },
    onCancel: () {
      listeners--;
      if (listeners <= 0) {
        listeners = 0;
        unawaited(upstream?.cancel());
        upstream = null;
      }
    },
  );
  ref.onDispose(controller.close);
  return controller.stream;
});

class OrderRepository {
  final ApiClient api;
  OrderRepository(this.api);

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
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/orders/',
      data: withKey({
        'items': items,
        'customer_id': ?customerId,
        if (promotionCode != null && promotionCode.isNotEmpty)
          'promotion_code': promotionCode,
        if (redeemPoints > 0) 'redeem_points': redeemPoints,
        if (destinationAddress != null && destinationAddress.isNotEmpty)
          'destination_address': destinationAddress,
        'destination_lat': ?destinationLat,
        'destination_lng': ?destinationLng,
      }, key: idempotencyKey ?? newIdempotencyKey()),
    );
    return Order.fromJson(resp.data!);
  }

  /// Adds a payment to an order. The backend responds with the created
  /// [PaymentLine] (not the whole order).
  Future<PaymentLine> addPayment({
    required int orderId,
    required String method,
    required int amountCents,
    String? idempotencyKey,
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/orders/$orderId/payments',
      data: withKey({
        'payment_method': method,
        'amount': amountCents / 100,
      }, key: idempotencyKey ?? newIdempotencyKey()),
    );
    return PaymentLine.fromJson(resp.data!);
  }

  Future<Order> addSplitPayments({
    required int orderId,
    required List<Map<String, String>> payments,
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/orders/$orderId/payments/split',
      data: {'payments': payments},
    );
    return Order.fromJson(resp.data!);
  }

  Future<List<Order>> recentOrders({int limit = 50}) async {
    final resp = await api.dio.get<List<dynamic>>(
      '/orders/',
      queryParameters: {'limit': limit},
    );
    return resp.data!
        .map((e) => Order.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<OrderReceipt> receipt(int orderId) async {
    final resp = await api.dio.get<Map<String, dynamic>>(
      '/orders/$orderId/receipt',
    );
    return OrderReceipt.fromJson(resp.data!);
  }

  Future<Order> cancel(int orderId) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/orders/$orderId/cancel',
    );
    return Order.fromJson(resp.data!);
  }

  Future<List<Order>> servingQueue({String? status}) async {
    final resp = await api.dio.get<List<dynamic>>(
      '/orders/serving/',
      queryParameters: {'status': ?status},
    );
    return resp.data!
        .map((e) => Order.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Order> startServing(int orderId) => _servingTransition(orderId, 'start');

  Future<Order> markReady(int orderId) => _servingTransition(orderId, 'ready');

  Future<Order> markServed(int orderId) => _servingTransition(orderId, 'serve');

  Future<Order> _servingTransition(int orderId, String action) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/orders/serving/$orderId/$action',
    );
    return Order.fromJson(resp.data!);
  }

  /// Server-Sent Events stream of serving transitions and tracking
  /// pings (`{"order_id": int, "serving_status": string}` or
  /// `{"order_id": int, "tracking_status": string, ...}`). Each emitted
  /// map carries the SSE event name under `event` (`serving` | `tracking`).
  /// Errors terminate the stream; callers fall back to polling.
  Stream<Map<String, dynamic>> servingEvents() async* {
    final resp = await api.dio.get<ResponseBody>(
      '/orders/serving/stream',
      options: Options(responseType: ResponseType.stream),
    );
    // Decode bytes and split into complete lines before parsing: TCP
    // chunks (and multi-byte UTF-8 characters) can split anywhere, so a
    // naive per-chunk parse corrupts frames that span chunk boundaries.
    var pending = '';
    var currentEvent = '';
    final data = StringBuffer();
    await for (final chunk in resp.data!.stream) {
      pending += utf8.decode(chunk, allowMalformed: true);
      while (true) {
        final nl = pending.indexOf('\n');
        if (nl < 0) break;
        final line = pending.substring(0, nl).replaceAll('\r', '');
        pending = pending.substring(nl + 1);
        if (line.startsWith('event: ')) {
          currentEvent = line.substring(7).trim();
        } else if (line.startsWith('data: ')) {
          if (currentEvent == 'serving' || currentEvent == 'tracking') {
            data.write(line.substring(6));
          }
        } else if (line.isEmpty) {
          if (data.isNotEmpty) {
            final payload = data.toString();
            data.clear();
            final emittedEvent = currentEvent;
            currentEvent = '';
            try {
              yield {
                ...jsonDecode(payload) as Map<String, dynamic>,
                'event': emittedEvent,
              };
            } on FormatException {
              // ignore malformed frames
            }
          }
        }
      }
    }
  }

  /// Active tracked orders for the tenant with latest positions.
  Future<List<TrackedOrder>> activeTracking() async {
    final resp = await api.dio.get<List<dynamic>>('/orders/tracking/');
    return (resp.data!)
        .map((e) => TrackedOrder.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Advance tracking: assigned -> en_route -> on_site (strict).
  Future<Order> trackingStatus({
    required int orderId,
    required String status,
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/orders/tracking/$orderId/status',
      data: {'status': status},
    );
    return Order.fromJson(resp.data!);
  }

  /// Append a position ping for a tracked order.
  Future<Map<String, dynamic>> reportLocation({
    required int orderId,
    required double lat,
    required double lng,
    String source = 'gps',
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/orders/tracking/$orderId/location',
      data: {'lat': lat, 'lng': lng, 'source': source},
    );
    return resp.data!;
  }

  /// Orders with destinations within [radiusKm] of a point (nearest first).
  Future<List<Map<String, dynamic>>> nearestTracking({
    required double lat,
    required double lng,
    double radiusKm = 10,
  }) async {
    final resp = await api.dio.get<List<dynamic>>(
      '/orders/tracking/nearest',
      queryParameters: {'lat': lat, 'lng': lng, 'radius_km': radiusKm},
    );
    return resp.data!.map((e) => e as Map<String, dynamic>).toList();
  }

  Future<Refund> createRefund({
    required int orderId,
    required List<Map<String, dynamic>> items,
    String? reason,
    String? paymentMethod,
    String? idempotencyKey,
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/refunds/',
      data: withKey({
        'order_id': orderId,
        'items': items,
        if (reason != null && reason.isNotEmpty) 'reason': reason,
        'payment_method': ?paymentMethod,
      }, key: idempotencyKey ?? newIdempotencyKey()),
    );
    return Refund.fromJson(resp.data!);
  }
}
