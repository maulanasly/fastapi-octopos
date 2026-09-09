/// 404 screen for unknown routes (GoRouter errorBuilder).
///
/// Rendered outside the shell, so it owns a full Scaffold with an
/// AppBar back affordance — unlike the bare PosScreen it replaces,
/// this screen always offers a way out.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/async_views.dart';
import '../core/strings.dart';

class NotFoundScreen extends ConsumerWidget {
  const NotFoundScreen({super.key, this.path});

  /// The unmatched path, shown as context. Null when unknown.
  final String? path;

  void _goPos(BuildContext context) {
    if (context.canPop()) {
      context.pop();
    } else {
      context.go('/pos');
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    return Scaffold(
      appBar: AppBar(
        leading: BackButton(onPressed: () => _goPos(context)),
        title: Text(s.of('pageNotFound')),
      ),
      body: BrandedEmptyState(
        message: path == null
            ? s.of('notFound')
            : s.of('pageNotFoundHint', args: {'path': path!}),
        title: s.of('pageNotFound'),
        action: () => context.go('/pos'),
        actionLabel: s.of('backToPos'),
      ),
    );
  }
}
