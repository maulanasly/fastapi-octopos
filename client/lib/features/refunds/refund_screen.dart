/// Refund flow: pick a recent completed order, select items, refund.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/async_views.dart';
import '../../core/strings.dart';
import '../../core/money.dart';
import '../../core/models.dart';

class RefundScreen extends ConsumerStatefulWidget {
  const RefundScreen({super.key});

  @override
  ConsumerState<RefundScreen> createState() => _RefundScreenState();
}

class _RefundScreenState extends ConsumerState<RefundScreen> {
  late Future<List<Order>> _ordersFuture;
  Order? _selected;
  final Map<int, int> _quantities = {};
  bool _submitting = false;
  String? _error;
  String? _success;

  @override
  void initState() {
    super.initState();
    _ordersFuture = ref.read(orderRepositoryProvider).recentOrders();
  }

  void _reload() {
    setState(() {
      _ordersFuture = ref.read(orderRepositoryProvider).recentOrders();
    });
  }

  Future<void> _submit() async {
    final s = ref.read(stringsProvider);
    final order = _selected;
    if (order == null) return;
    final items = <Map<String, dynamic>>[];
    for (final item in order.items) {
      final qty = _quantities[item.id] ?? 0;
      if (qty > 0) {
        items.add({'order_item_id': item.id, 'quantity': qty});
      }
    }
    if (items.isEmpty) {
      setState(() => _error = s.of('selectAtLeastOne'));
      return;
    }
    setState(() {
      _submitting = true;
      _error = null;
      _success = null;
    });
    try {
      await ref
          .read(orderRepositoryProvider)
          .createRefund(
            orderId: order.id,
            items: items,
            paymentMethod: order.payments.isNotEmpty
                ? order.payments.first.paymentMethod
                : 'cash',
          );
      setState(() {
        _success = 'Refund created';
        _selected = null;
        _quantities.clear();
      });
      _ordersFuture = ref.read(orderRepositoryProvider).recentOrders();
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    return Scaffold(
      appBar: AppBar(title: Text(s.of('refunds'))),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 640),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                if (_error != null)
                  Text(
                    _error!,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.error,
                    ),
                  ),
                if (_success != null)
                  Text(
                    _success!,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.primary,
                    ),
                  ),
                const SizedBox(height: 8),
                Expanded(
                  child: _selected == null
                      ? _orderList(context)
                      : _itemsView(context),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _orderList(BuildContext context) {
    final s = ref.read(stringsProvider);
    return FutureBuilder<List<Order>>(
      future: _ordersFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return ErrorStateView(
            message: s.of('genericError'),
            onRetry: _reload,
          );
        }
        final orders = snapshot.data ?? [];
        final refundable = orders
            .where((o) => o.status == 'serving' || o.status == 'completed')
            .toList();
        if (refundable.isEmpty) {
          return EmptyStateView(message: s.of('noCompletedOrders'));
        }
        return ListView.separated(
          itemCount: refundable.length,
          separatorBuilder: (_, _) => const Divider(height: 8),
          itemBuilder: (context, i) {
            final order = refundable[i];
            return ListTile(
              title: Text('Order #${order.id}'),
              subtitle: Text(
                '${formatCents(centsFromApi(order.grandTotalAmount))} — '
                '${order.items.length} item(s)',
              ),
              trailing: const Icon(Icons.chevron_right),
              onTap: () {
                setState(() {
                  _selected = order;
                  _quantities.clear();
                  for (final item in order.items) {
                    _quantities[item.id] = 0;
                  }
                });
              },
            );
          },
        );
      },
    );
  }

  Widget _itemsView(BuildContext context) {
    final s = ref.watch(stringsProvider);
    final order = _selected!;
    final total = order.items.fold<int>(0, (sum, item) {
      return sum + centsFromApi(item.unitPrice) * (_quantities[item.id] ?? 0);
    });
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Text(
              'Order #${order.id}',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const Spacer(),
            TextButton(
              onPressed: () => setState(() => _selected = null),
              child: Text(s.of('back')),
            ),
          ],
        ),
        Expanded(
          child: ListView.separated(
            itemCount: order.items.length,
            separatorBuilder: (_, _) => const Divider(height: 8),
            itemBuilder: (context, i) {
              final item = order.items[i];
              return ListTile(
                dense: true,
                title: Text(s.of('productId', args: {'id': item.productId})),
                subtitle: Text(
                  '${item.quantity} × ${formatCents(centsFromApi(item.unitPrice))}',
                ),
                trailing: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    IconButton(
                      icon: const Icon(Icons.remove_circle_outline),
                      onPressed: () {
                        final qty = _quantities[item.id] ?? 0;
                        setState(
                          () => _quantities[item.id] = (qty - 1).clamp(
                            0,
                            item.quantity,
                          ),
                        );
                      },
                    ),
                    Text('${_quantities[item.id] ?? 0}'),
                    IconButton(
                      icon: const Icon(Icons.add_circle_outline),
                      onPressed: () {
                        final qty = _quantities[item.id] ?? 0;
                        setState(
                          () => _quantities[item.id] = (qty + 1).clamp(
                            0,
                            item.quantity,
                          ),
                        );
                      },
                    ),
                  ],
                ),
              );
            },
          ),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Text(
            s.of('refundTotal', args: {'total': formatCents(total)}),
            style: Theme.of(context).textTheme.titleMedium,
          ),
        ),
        FilledButton(
          onPressed: _submitting ? null : _submit,
          child: _submitting
              ? const SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : Text(ref.watch(stringsProvider).of('refundSelectedItems')),
        ),
      ],
    );
  }
}
