/// One-shot navigation notices.
///
/// GoRouter `redirect` has no Scaffold context, so it cannot show a
/// SnackBar directly. Instead it stashes a strings key here; [HomeShell]
/// (always present on shell routes) displays it once and clears it.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

class NavNotice extends Notifier<String?> {
  @override
  String? build() => null;

  void show(String key) => state = key;
  void clear() => state = null;
}

final navNoticeProvider = NotifierProvider<NavNotice, String?>(
  NavNotice.new,
);

/// Deep link (or pre-login location) to land on after sign-in.
///
/// Stashed by the router guard while signed out; consumed once on the
/// login→signed-in transition. The permission gate still applies, so a
/// stale privileged bookmark degrades to POS with a notice.
class PendingRedirect extends Notifier<String?> {
  @override
  String? build() => null;

  void save(String path) => state = path;

  String? consume() {
    final pending = state;
    state = null;
    return pending;
  }
}

final pendingRedirectProvider = NotifierProvider<PendingRedirect, String?>(
  PendingRedirect.new,
);
