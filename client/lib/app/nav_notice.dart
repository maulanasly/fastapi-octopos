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
