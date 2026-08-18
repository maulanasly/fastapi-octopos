/// Serving queue screen: kitchen/prep display of paid orders waiting to
/// be prepared and handed over. Polls via SSE with a 10s fallback.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/errors.dart';
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
      return Center(
        child: state.loading
            ? const CircularProgressIndicator()
            : Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.room_service_outlined,
                    size: 56,
                    color: Theme.of(context).colorScheme.outline,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    s.of('servingEmpty'),
                    style: Theme.of(context).textTheme.bodyLarge,
                  ),
                ],
              ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(12),
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
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(12),
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
            const SizedBox(height: 8),
            for (final item in order.items)
              Text(
                '${item.quantity}× ${item.product?.name ?? ''}',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            const SizedBox(height: 8),
            Text(
              s.of('itemsCount', args: {'count': order.items.length}),
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 4),
            Text(
              formatCents((order.totalAmount * 100).round()),
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 8),
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
                      icon: const Icon(Icons.check_circle_outline, size: 18),
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
    final (labelKey, color) = switch (status) {
      'queued' => ('statusQueued', Colors.orange),
      'preparing' => ('statusPreparing', Colors.blue),
      'ready' => ('statusReady', Colors.green),
      'served' => ('statusServed', Colors.grey),
      _ => (null, Colors.grey),
    };
    return Chip(
      label: Text(labelKey == null ? status : s.of(labelKey)),
      labelStyle: TextStyle(
        color: color,
        fontSize: 12,
        fontWeight: FontWeight.w600,
      ),
      visualDensity: VisualDensity.compact,
      side: BorderSide(color: color.withValues(alpha: 0.4)),
      backgroundColor: color.withValues(alpha: 0.08),
    );
  }
}
