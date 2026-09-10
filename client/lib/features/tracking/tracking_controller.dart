/// Tracking controller: active service trips, live positions via the
/// shared SSE event bus and a polling fallback.
library;

import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/auth_controller.dart';
import '../../core/errors.dart';
import '../../core/models.dart';
import '../../core/strings.dart';

final trackingControllerProvider =
    NotifierProvider<TrackingController, TrackingState>(TrackingController.new);

class TrackingState {
  const TrackingState({this.trips = const [], this.loading = false, this.error});

  final List<TrackedOrder> trips;
  final bool loading;

  /// Last refresh failure, if any. Shown only when there are no trips;
  /// stale trips keep rendering while [error] records the failure.
  final String? error;

  TrackingState copyWith({
    List<TrackedOrder>? trips,
    bool? loading,
    String? Function()? error,
  }) => TrackingState(
    trips: trips ?? this.trips,
    loading: loading ?? this.loading,
    error: error != null ? error() : this.error,
  );
}

class TrackingController extends Notifier<TrackingState> {
  StreamSubscription<Map<String, dynamic>>? _sseSub;
  Timer? _pollTimer;
  bool _subscribed = false;

  @override
  TrackingState build() {
    ref.onDispose(() {
      _teardown();
    });
    // The SSE subscription and poll timer must not outlive the session:
    // sign-out tears them down, sign-in brings them back.
    ref.listen<AuthState>(authControllerProvider, (prev, next) {
      if (prev?.status == AuthStatus.signedIn &&
          next.status == AuthStatus.signedOut) {
        _teardown();
        state = const TrackingState();
      } else if (next.status == AuthStatus.signedIn &&
          prev?.status != AuthStatus.signedIn) {
        _subscribe();
      }
    });
    if (!_subscribed) {
      _subscribe();
    }
    return const TrackingState();
  }

  void _subscribe() {
    if (_subscribed && _sseSub != null) return;
    _subscribed = true;
    _sseSub = ref.read(servingEventBusProvider).listen(
      (event) {
        if (event['event'] == 'tracking') refresh();
      },
      onError: (_) => _startPolling(),
      onDone: () {
        _sseSub = null;
        _startPolling();
      },
    );
    refresh();
  }

  void _startPolling() {
    _pollTimer ??= Timer.periodic(const Duration(seconds: 10), (_) => refresh());
  }

  void _teardown() {
    _pollTimer?.cancel();
    _pollTimer = null;
    unawaited(_sseSub?.cancel());
    _sseSub = null;
    _subscribed = false;
  }

  Future<void> refresh() async {
    try {
      final trips = await ref.read(orderRepositoryProvider).activeTracking();
      state = state.copyWith(trips: trips, error: () => null);
    } catch (e) {
      // Keep the last known trips on transient failures, but record
      // the error so an empty list can offer a retry.
      state = state.copyWith(
        error: () => friendlyError(e, ref.read(stringsProvider)),
      );
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
