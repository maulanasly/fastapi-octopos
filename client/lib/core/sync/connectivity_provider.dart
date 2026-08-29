import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final connectivityProvider = StreamProvider<ConnectivityResult>((ref) async* {
  final conn = Connectivity();
  final initial = await conn.checkConnectivity();
  yield initial.contains(ConnectivityResult.none) ? ConnectivityResult.none : initial.first;
  await for (final result in conn.onConnectivityChanged) {
    if (result.contains(ConnectivityResult.none) || result.isEmpty) {
      yield ConnectivityResult.none;
    } else {
      yield result.first;
    }
  }
});

final isOnlineProvider = Provider<bool>((ref) {
  final async = ref.watch(connectivityProvider);
  return async.maybeWhen(data: (r) => r != ConnectivityResult.none, orElse: () => true);
});
