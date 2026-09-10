/// Orders the sync engine gave up on: per-row retry (re-queues and
/// immediately runs a sync pass) and discard. Watches the failed stream
/// so rows disappear as they resolve.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/async_views.dart';
import '../../core/errors.dart';
import '../../core/layout.dart';
import '../../core/strings.dart';
import '../../core/sync/outbox_providers.dart';
import '../../core/sync/outbox_repository.dart';
import '../../core/sync/sync_service.dart';

class FailedOrdersDialog extends ConsumerWidget {
  const FailedOrdersDialog({super.key});

  Future<void> _retryRow(
    BuildContext context,
    WidgetRef ref,
    AppStrings s,
    int id,
  ) async {
    try {
      await ref.read(outboxRepositoryProvider).retry(id);
      await ref.read(syncServiceProvider).syncOutbox();
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(friendlyError(e, s))),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    final failedAsync = ref.watch(failedOutboxProvider);
    return AlertDialog(
      title: Text(s.of('failedOrders')),
      content: SizedBox(
        width: dialogWidth(context),
        child: failedAsync.when(
          loading: () => const LoadingStateView(),
          // Drift streams effectively never error; show the message
          // without a retry action that could not help.
          error: (e, _) => Text(friendlyError(e, s)),
          data: (rows) => rows.isEmpty
              ? Text(s.of('noFailedOrders'))
              : Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Flexible(
                      child: ListView.separated(
                        shrinkWrap: true,
                        itemCount: rows.length,
                        separatorBuilder: (_, _) => const Divider(height: 8),
                        itemBuilder: (context, i) {
                          final row = rows[i];
                          return ListTile(
                            dense: true,
                            contentPadding: EdgeInsets.zero,
                            title: Text(
                              s.of('orderId', args: {'id': row.id}),
                            ),
                            subtitle: Text(
                              outboxRowErrorMessage(row.lastError, s),
                            ),
                            trailing: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                IconButton(
                                  tooltip: s.of('retry'),
                                  icon: const Icon(Icons.refresh, size: 20),
                                  visualDensity: VisualDensity.compact,
                                  onPressed: () =>
                                      _retryRow(context, ref, s, row.id),
                                ),
                                IconButton(
                                  tooltip: s.of('discard'),
                                  icon: const Icon(
                                    Icons.delete_outline,
                                    size: 20,
                                  ),
                                  visualDensity: VisualDensity.compact,
                                  onPressed: () => ref
                                      .read(outboxRepositoryProvider)
                                      .remove(row.id),
                                ),
                              ],
                            ),
                          );
                        },
                      ),
                    ),
                  ],
                ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: Text(s.of('done')),
        ),
      ],
    );
  }
}
