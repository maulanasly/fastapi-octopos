/// Order history: list, status filter, cancel pending, reprint receipts.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/dates.dart';
import '../../core/errors.dart';
import '../../core/money.dart';
import '../../core/models.dart';
import '../../core/strings.dart';
import '../pos/receipt_screen.dart';

class OrdersScreen extends ConsumerStatefulWidget {
  const OrdersScreen({super.key});

  @override
  ConsumerState<OrdersScreen> createState() => _OrdersScreenState();
}

class _OrdersScreenState extends ConsumerState<OrdersScreen> {
  String? _statusFilter;
  late Future<List<Order>> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<List<Order>> _load() =>
      ref.read(orderRepositoryProvider).recentOrders();

  void _reload() {
    setState(() => _future = _load());
  }

  Future<void> _cancel(Order order) async {
    final s = ref.read(stringsProvider);
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(s.of('cancelOrder')),
        content: Text(s.of('confirmCancel')),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text(s.of('cancel')),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: Text(s.of('cancelOrder')),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    try {
      await ref.read(orderRepositoryProvider).cancel(order.id);
      _reload();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(friendlyError(e, s))));
    }
  }

  void _reprint(Order order) {
    Navigator.of(
      context,
    ).push(MaterialPageRoute(builder: (_) => ReceiptScreen(orderId: order.id)));
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(s.of('orders')),
        actions: [
          IconButton(
            tooltip: s.of('orders'),
            icon: const Icon(Icons.refresh),
            onPressed: _reload,
          ),
        ],
      ),
      body: Column(
        children: [
          SizedBox(
            height: 48,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 8),
              children: [
                _filterChip(s, null, s.of('all'), 'filter-all'),
                _filterChip(
                  s,
                  'pending',
                  s.of('statusPending'),
                  'filter-pending',
                ),
                _filterChip(
                  s,
                  'serving',
                  s.of('statusServing'),
                  'filter-serving',
                ),
                _filterChip(
                  s,
                  'completed',
                  s.of('statusCompleted'),
                  'filter-completed',
                ),
                _filterChip(
                  s,
                  'cancelled',
                  s.of('statusCancelled'),
                  'filter-cancelled',
                ),
              ],
            ),
          ),
          Expanded(
            child: FutureBuilder<List<Order>>(
              future: _future,
              builder: (context, snapshot) {
                if (snapshot.connectionState != ConnectionState.done) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snapshot.hasError) {
                  return Center(child: Text(friendlyError(snapshot.error!, s)));
                }
                final all = snapshot.data ?? [];
                final visible = _statusFilter == null
                    ? all
                    : all.where((o) => o.status == _statusFilter).toList();
                if (visible.isEmpty) {
                  return Center(child: Text(s.of('noOrders')));
                }
                return RefreshIndicator(
                  onRefresh: () async => _reload(),
                  child: ListView.separated(
                    padding: const EdgeInsets.all(16),
                    itemCount: visible.length,
                    separatorBuilder: (_, _) => const Divider(height: 8),
                    itemBuilder: (context, i) =>
                        _orderTile(context, visible[i]),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _filterChip(
    AppStrings s,
    String? value,
    String label,
    String keyName,
  ) {
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: ChoiceChip(
        key: Key(keyName),
        label: Text(label),
        selected: _statusFilter == value,
        onSelected: (_) => setState(() => _statusFilter = value),
      ),
    );
  }

  Widget _orderTile(BuildContext context, Order order) {
    final s = ref.read(stringsProvider);
    final statusLabel = switch (order.status) {
      'serving' => s.of('statusServing'),
      'completed' => s.of('statusCompleted'),
      'cancelled' => s.of('statusCancelled'),
      _ => s.of('statusPending'),
    };
    return Card(
      margin: EdgeInsets.zero,
      child: ListTile(
        title: Text(s.of('orderId', args: {'id': order.id})),
        subtitle: Text(
          '${formatDateTimeIso(order.createdAt)}\n'
          '${s.of('itemsCount', args: {'count': order.items.length})}'
          ' · ${formatCents(centsFromApi(order.grandTotalAmount))}',
        ),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Chip(
              label: Text(statusLabel),
              visualDensity: VisualDensity.compact,
            ),
            if (order.servingStatus != 'none' && order.servingStatus != 'served')
              Chip(
                label: Text(_servingLabel(s, order.servingStatus)),
                visualDensity: VisualDensity.compact,
                backgroundColor: Theme.of(context)
                    .colorScheme
                    .secondaryContainer
                    .withValues(alpha: 0.5),
              ),
            IconButton(
              tooltip: s.of('reprint'),
              icon: const Icon(Icons.receipt_long),
              onPressed: () => _reprint(order),
            ),
            if (order.status == 'pending')
              IconButton(
                tooltip: s.of('cancelOrder'),
                icon: const Icon(Icons.cancel_outlined),
                onPressed: () => _cancel(order),
              ),
          ],
        ),
        onTap: () => _reprint(order),
      ),
    );
  }
}

String _servingLabel(AppStrings s, String status) => switch (status) {
  'queued' => s.of('statusQueued'),
  'preparing' => s.of('statusPreparing'),
  'ready' => s.of('statusReady'),
  _ => status,
};
