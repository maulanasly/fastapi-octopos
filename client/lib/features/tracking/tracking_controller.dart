/// Tracking controller: active service trips, live positions via SSE
/// (shared stream with the serving queue) and a polling fallback.
library;

import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/models.dart';

final trackingControllerProvider =
    NotifierProvider<TrackingController, TrackingState>(TrackingController.new);

class TrackingState {
  const TrackingState({this.trips = const [], this.loading = false});

  final List<TrackedOrder> trips;
  final bool loading;

  TrackingState copyWith({List<TrackedOrder>? trips, bool? loading}) =>
      TrackingState(
        trips: trips ?? this.trips,
        loading: loading ?? this.loading,
      );
}

class TrackingController extends Notifier<TrackingState> {
  StreamSubscription<Map<String, dynamic>>? _sseSub;
  Timer? _pollTimer;
  bool _subscribed = false;

  @override
  TrackingState build() {
    ref.onDispose(() {
      _sseSub?.cancel();
      _pollTimer?.cancel();
    });
    if (!_subscribed) {
      _subscribed = true;
      _subscribe();
    }
    return const TrackingState();
  }

  void _subscribe() {
    final repo = ref.read(orderRepositoryProvider);
    _sseSub = repo.servingEvents().listen(
      (event) {
        if (event['event'] == 'tracking') refresh();
      },
      onError: (_) => _startPolling(),
      onDone: _startPolling,
    );
    refresh();
  }

  void _startPolling() {
    _pollTimer ??= Timer.periodic(const Duration(seconds: 10), (_) => refresh());
  }

  Future<void> refresh() async {
    try {
      final trips = await ref.read(orderRepositoryProvider).activeTracking();
      state = state.copyWith(trips: trips);
    } catch (_) {
      // keep last known trips on transient failures
    }
  }

  /// Advance tracking: assigned -> en_route -> on_site.
  Future<void> transition(int orderId, String status) async {
    await ref.read(orderRepositoryProvider).trackingStatus(
      orderId: orderId,
      status: status,
    );
    await refresh();
  }

  /// Report the device position for a trip.
  Future<void> reportPosition({
    required int orderId,
    required double lat,
    required double lng,
    String source = 'gps',
  }) async {
    await ref.read(orderRepositoryProvider).reportLocation(
      orderId: orderId,
      lat: lat,
      lng: lng,
      source: source,
    );
    await refresh();
  }
}
