/// Serving queue controller: keeps the kitchen queue fresh via SSE with a
/// polling fallback, and applies Start/Ready/Serve transitions.
library;

import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/auth_controller.dart';
import '../../core/errors.dart';
import '../../core/models.dart';
import '../../core/strings.dart';

final servingControllerProvider =
    NotifierProvider<ServingController, ServingState>(ServingController.new);

class ServingState {
  const ServingState({this.orders = const [], this.loading = false, this.error});

  final List<Order> orders;
  final bool loading;

  /// Last refresh failure, if any. Shown only when the queue is empty;
  /// a stale queue keeps rendering while [error] records the failure.
  final String? error;

  ServingState copyWith({
    List<Order>? orders,
    bool? loading,
    String? Function()? error,
  }) => ServingState(
    orders: orders ?? this.orders,
    loading: loading ?? this.loading,
    error: error != null ? error() : this.error,
  );
}

class ServingController extends Notifier<ServingState> {
  StreamSubscription<Map<String, dynamic>>? _sseSub;
  Timer? _pollTimer;
  bool _subscribed = false;

  @override
  ServingState build() {
    ref.onDispose(() {
      _teardown();
    });
    // The SSE subscription and poll timer must not outlive the session:
    // sign-out tears them down, sign-in brings them back.
    ref.listen<AuthState>(authControllerProvider, (prev, next) {
      if (prev?.status == AuthStatus.signedIn &&
          next.status == AuthStatus.signedOut) {
        _teardown();
        state = const ServingState();
      } else if (next.status == AuthStatus.signedIn &&
          prev?.status != AuthStatus.signedIn) {
        _subscribe();
      }
    });
    if (!_subscribed) {
      _subscribe();
    }
    return const ServingState();
  }

  void _subscribe() {
    if (_subscribed && _sseSub != null) return;
    _subscribed = true;
    _sseSub = ref.read(servingEventBusProvider).listen(
      (_) => refresh(),
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
      final orders = await ref.read(orderRepositoryProvider).servingQueue();
      state = state.copyWith(orders: orders, error: () => null);
    } catch (e) {
      // Keep the last known queue on transient failures, but record
      // the error so an empty queue can offer a retry.
      state = state.copyWith(
        error: () => friendlyError(e, ref.read(stringsProvider)),
      );
    }
  }

  Future<void> start(int orderId) =>
      _transition(() => ref.read(orderRepositoryProvider).startServing(orderId));

  Future<void> ready(int orderId) =>
      _transition(() => ref.read(orderRepositoryProvider).markReady(orderId));

  Future<void> serve(int orderId) =>
      _transition(() => ref.read(orderRepositoryProvider).markServed(orderId));

  Future<void> _transition(Future<Order> Function() action) async {
    await action();
    await refresh();
  }
}
