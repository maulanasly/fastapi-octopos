/// Serving queue controller: keeps the kitchen queue fresh via SSE with a
/// polling fallback, and applies Start/Ready/Serve transitions.
library;

import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/models.dart';

final servingControllerProvider =
    NotifierProvider<ServingController, ServingState>(ServingController.new);

class ServingState {
  const ServingState({this.orders = const [], this.loading = false});

  final List<Order> orders;
  final bool loading;

  ServingState copyWith({List<Order>? orders, bool? loading}) =>
      ServingState(orders: orders ?? this.orders, loading: loading ?? this.loading);
}

class ServingController extends Notifier<ServingState> {
  StreamSubscription<Map<String, dynamic>>? _sseSub;
  Timer? _pollTimer;
  bool _subscribed = false;

  @override
  ServingState build() {
    ref.onDispose(() {
      _sseSub?.cancel();
      _pollTimer?.cancel();
    });
    if (!_subscribed) {
      _subscribed = true;
      _subscribe();
    }
    return const ServingState();
  }

  void _subscribe() {
    final repo = ref.read(orderRepositoryProvider);
    _sseSub = repo.servingEvents().listen(
      (_) => refresh(),
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
      final orders = await ref.read(orderRepositoryProvider).servingQueue();
      state = state.copyWith(orders: orders);
    } catch (_) {
      // keep last known queue on transient failures
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