/// Serving queue screen: kitchen/prep display of paid orders waiting to
/// be prepared and handed over. Polls via SSE with a 10s fallback.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/theme.dart';
import '../../core/app_icons.dart';
import '../../core/async_views.dart';
import '../../core/errors.dart';
import '../../core/layout.dart';
import '../../core/money.dart';
import '../../core/strings.dart';
import 'serving_controller.dart';

class ServingScreen extends ConsumerWidget {
  const ServingScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    final state = ref.watch(servingControllerProvider);
    final orders = state.orders;

    if (orders.isEmpty) {
      if (state.loading) return const LoadingStateView();
      return BrandedEmptyState(
        message: s.of('servingEmptyHint'),
        illustration: 'assets/illustrations/empty-cart.svg',
        title: s.of('servingEmpty'),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(AppSpacing.md),
      itemCount: orders.length,
      itemBuilder: (context, index) =>
          _ServingCard(order: orders[index]),
    );
  }
}

class _ServingCard extends ConsumerWidget {
  const _ServingCard({required this.order});

  final dynamic order;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    final controller = ref.read(servingControllerProvider.notifier);

    return Card(
      margin: const EdgeInsets.only(bottom: AppSpacing.md),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(
                  s.of('orderNumber', args: {'id': order.id}),
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const Spacer(),
                _StatusChip(status: order.servingStatus),  ],
            ),
            if (order.customer?.name != null)
              Padding(
                padding: const EdgeInsets.only(top: 2),
                child: Text(
                  order.customer!.name,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ),
            const SizedBox(height: AppSpacing.sm),
            for (final item in order.items)
              Text(
                '${item.quantity}× ${item.product?.name ?? ''}',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            const SizedBox(height: AppSpacing.sm),
            Text(
              s.of('itemsCount', args: {'count': order.items.length}),
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 4),
            Text(
              formatCents((order.totalAmount * 100).round()),
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: AppSpacing.sm),
            Row(
              children: [
                if (order.servingStatus == 'queued')
                  Expanded(
                    child: FilledButton.icon(
                      icon: const Icon(Icons.play_arrow, size: 18),
                      label: Text(s.of('startPreparing')),
                      onPressed: () {
                        _runTransition(context, ref, () => controller.start(order.id));
                      },
                    ),
                  ),
                if (order.servingStatus == 'preparing')
                  Expanded(
                    child: FilledButton.icon(
                      icon: const Icon(AppIcons.checkCircle, size: 18),
                      label: Text(s.of('markReady')),
                      onPressed: () {
                        _runTransition(context, ref, () => controller.ready(order.id));
                      },
                    ),
                  ),
                if (order.servingStatus == 'ready')
                  Expanded(
                    child: FilledButton.icon(
                      icon: const Icon(Icons.room_service, size: 18),
                      label: Text(s.of('markServed')),
                      onPressed: () {
                        _runTransition(context, ref, () => controller.serve(order.id));
                      },
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  void _runTransition(
    BuildContext context,
    WidgetRef ref,
    Future<void> Function() action,
  ) async {
    try {
      await action();
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(friendlyError(e, ref.read(stringsProvider)))),
        );
      }
    }
  }
}

class _StatusChip extends ConsumerWidget {
  const _StatusChip({required this.status});

  final String status;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    final scheme = Theme.of(context).colorScheme;
    final (labelKey, color) = switch (status) {
      'queued' => ('statusQueued', AppColors.warning),
      'preparing' => ('statusPreparing', AppColors.secondaryLight),
      'ready' => ('statusReady', AppColors.success),
      'served' => ('statusServed', scheme.outline),
      _ => (null, scheme.outline),
    };
    // For served/grey, ensure text is onSurfaceVariant for contrast in dark mode.
    final isServedGrey = status == 'served' || labelKey == null;
    final textColor = isServedGrey ? scheme.onSurfaceVariant : color;
    return Chip(
      label: Text(labelKey == null ? status : s.of(labelKey)),
      labelStyle: TextStyle(
        color: textColor,
        fontSize: 12,
        fontWeight: FontWeight.w600,
      ),
      visualDensity: VisualDensity.compact,
      side: BorderSide(color: color.withValues(alpha: 0.4)),
      backgroundColor: color.withValues(alpha: 0.08),
    );
  }
}
