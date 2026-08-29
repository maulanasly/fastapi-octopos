import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'connectivity_provider.dart';
import 'sync_service.dart';

/// Watches connectivity and triggers outbox + catalog sync when coming online.
/// Place a `ref.watch(autoSyncProvider)` in app root to activate.
final autoSyncProvider = Provider<void>((ref) {
  ref.listen(isOnlineProvider, (prev, next) async {
    if (next && prev == false) {
      // Transition offline -> online
      try {
        await ref.read(syncServiceProvider).syncAll();
      } catch (_) {}
    }
  });
  // Also attempt periodic foreground sync every 5 minutes via timer is handled by workmanager;
  // here we just ensure initial online sync.
});
