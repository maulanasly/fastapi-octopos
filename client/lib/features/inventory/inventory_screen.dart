/// Inventory: stock movements, replenishment suggestions, manual adjust.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/auth_controller.dart';
import '../../core/dates.dart';
import '../../core/errors.dart';
import '../../core/models.dart';
import '../../core/strings.dart';
import '../pos/catalog_controller.dart';

class InventoryScreen extends ConsumerStatefulWidget {
  const InventoryScreen({super.key});

  @override
  ConsumerState<InventoryScreen> createState() => _InventoryScreenState();
}

class _InventoryScreenState extends ConsumerState<InventoryScreen> {
  int _tab = 0;
  late Future<List<StockMovement>> _movements;
  late Future<List<ReplenishmentSuggestion>> _suggestions;
  String? _typeFilter;
  bool _onlyReorder = true;
  List<Supplier> _suppliers = const [];
  final Map<int, _SuggestionRow> _rows = {};
  bool _generating = false;

  @override
  void initState() {
    super.initState();
    _reload();
  }

  void _reload() {
    _movements = ref
        .read(inventoryRepositoryProvider)
        .movements(movementType: _typeFilter);
    _suggestions = ref
        .read(inventoryRepositoryProvider)
        .suggestions(onlyReorder: _onlyReorder);
    _rows.clear();
    _loadSuppliers();
  }

  Future<void> _loadSuppliers() async {
    try {
      final all = await ref.read(purchasingRepositoryProvider).suppliers();
      if (!mounted) return;
      setState(() => _suppliers = all.where((x) => x.isActive).toList());
    } catch (_) {
      if (mounted) setState(() => _suppliers = const []);
    }
  }

  void _syncRows(List<ReplenishmentSuggestion> suggestions) {
    for (final item in suggestions) {
      _rows.putIfAbsent(
        item.productId,
        () => _SuggestionRow(
          name: item.productName,
          qty: TextEditingController(
            text: item.recommendedOrderQuantity > 0
                ? '${item.recommendedOrderQuantity}'
                : '',
          ),
          cost: TextEditingController(text: item.unitCost.toString()),
          supplierId: item.suggestedSupplierId,
        ),
      );
    }
    _rows.removeWhere((productId, _) {
      final stale = suggestions.every((item) => item.productId != productId);
      if (stale) {
        _rows[productId]?.qty.dispose();
        _rows[productId]?.cost.dispose();
      }
      return stale;
    });
  }

  Future<void> _adjust(ReplenishmentSuggestion suggestion) async {
    final s = ref.read(stringsProvider);
    final delta = TextEditingController(
      text: suggestion.recommendedOrderQuantity > 0
          ? '${suggestion.recommendedOrderQuantity}'
          : '',
    );
    final note = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('${s.of('adjustStock')}: ${suggestion.productName}'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              '${s.of('qtyBefore')}: ${suggestion.currentStock} · '
              '${s.of('recommendedQty', args: {'qty': suggestion.recommendedOrderQuantity})}',
            ),
            TextField(
              controller: delta,
              keyboardType: TextInputType.number,
              decoration: InputDecoration(
                labelText: s.of('adjustDelta'),
                isDense: true,
              ),
            ),
            TextField(
              controller: note,
              decoration: InputDecoration(
                labelText: s.of('adjustNote'),
                isDense: true,
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text(s.of('cancel')),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: Text(s.of('save')),
          ),
        ],
      ),
    );
    if (ok != true) return;
    final parsed = int.tryParse(delta.text.trim());
    if (parsed == null || parsed == 0) return;
    try {
      await ref.read(catalogRepositoryProvider).updateProduct(
        suggestion.productId,
        {'stock_quantity': suggestion.currentStock + parsed},
      );
      await ref.read(catalogControllerProvider.notifier).refresh();
      if (mounted) setState(_reload);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(friendlyError(e, s))));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    final canAdjust = ref.watch(authControllerProvider).has('products:manage');
    final canGenerate = ref.watch(authControllerProvider).has(
      'purchasing:manage',
    );

    return Scaffold(
      appBar: AppBar(
        title: Text(s.of('inventory')),
        actions: [
          IconButton(
            tooltip: s.of('inventory'),
            icon: const Icon(Icons.refresh),
            onPressed: () => setState(_reload),
          ),
        ],
      ),
      body: Column(
        children: [
          SegmentedButton<int>(
            segments: [
              ButtonSegment(
                value: 0,
                label: Text(s.of('movements')),
                icon: const Icon(Icons.swap_vert, size: 16),
              ),
              ButtonSegment(
                value: 1,
                label: Text(s.of('replenishment')),
                icon: const Icon(Icons.trending_up, size: 16),
              ),
            ],
            selected: {_tab},
            onSelectionChanged: (v) => setState(() => _tab = v.first),
          ),
          if (_tab == 0) _typeFilterRow(s),
          Expanded(
            child: _tab == 0
                ? _movementsView(context, s)
                : _suggestionsView(context, s, canAdjust, canGenerate),
          ),
        ],
      ),
    );
  }

  Widget _typeFilterRow(AppStrings s) {
    return SizedBox(
      height: 44,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 8),
        children: [
          _typeChip(s, null, s.of('all')),
          _typeChip(s, 'sale', 'sale'),
          _typeChip(s, 'refund', 'refund'),
          _typeChip(s, 'manual_adjustment', 'manual'),
          _typeChip(s, 'initial_stock', 'initial'),
        ],
      ),
    );
  }

  Widget _typeChip(AppStrings s, String? value, String label) {
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: ChoiceChip(
        label: Text(label),
        selected: _typeFilter == value,
        onSelected: (_) => setState(() {
          _typeFilter = value;
          _reload();
        }),
      ),
    );
  }

  Widget _movementsView(BuildContext context, AppStrings s) {
    return FutureBuilder<List<StockMovement>>(
      future: _movements,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return Center(child: Text(friendlyError(snapshot.error!, s)));
        }
        final movements = snapshot.data ?? [];
        if (movements.isEmpty) {
          return Center(child: Text(s.of('noMovements')));
        }
        return ListView.separated(
          padding: const EdgeInsets.all(16),
          itemCount: movements.length,
          separatorBuilder: (_, _) => const Divider(height: 8),
          itemBuilder: (context, i) {
            final m = movements[i];
            final delta = m.quantityDelta;
            return ListTile(
              leading: Icon(
                delta >= 0
                    ? Icons.add_box_outlined
                    : Icons.remove_circle_outline,
                color: delta >= 0 ? Colors.green : Colors.red,
              ),
              title: Text(
                '${s.of('productId', args: {'id': m.productId})} · ${m.movementType}',
              ),
              subtitle: Text(
                '${formatDateTimeIso(m.createdAt)}'
                '${m.note != null ? ' — ${m.note}' : ''}',
              ),
              trailing: Text(
                '${m.quantityBefore} → ${m.quantityAfter} (${delta >= 0 ? '+' : ''}$delta)',
              ),
            );
          },
        );
      },
    );
  }

  Widget _suggestionsView(
    BuildContext context,
    AppStrings s,
    bool canAdjust,
    bool canGenerate,
  ) {
    return Column(
      children: [
        Row(
          children: [
            Checkbox(
              value: _onlyReorder,
              onChanged: (v) => setState(() {
                _onlyReorder = v ?? true;
                _reload();
              }),
            ),
            Text(s.of('replenishment')),
          ],
        ),
        Expanded(
          child: FutureBuilder<List<ReplenishmentSuggestion>>(
            future: _suggestions,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snapshot.hasError) {
                return Center(child: Text(friendlyError(snapshot.error!, s)));
              }
              final suggestions = snapshot.data ?? [];
              _syncRows(suggestions);
              if (suggestions.isEmpty) {
                return Center(child: Text(s.of('noSuggestions')));
              }
              return ListView.separated(
                padding: const EdgeInsets.all(16),
                itemCount: suggestions.length,
                separatorBuilder: (_, _) => const Divider(height: 8),
                itemBuilder: (context, i) =>
                    _suggestionRow(context, s, suggestions[i], canAdjust),
              );
            },
          ),
        ),
        if (canGenerate)
          Padding(
            padding: const EdgeInsets.all(12),
            child: FilledButton.icon(
              onPressed: _generating ? null : _generate,
              icon: _generating
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.playlist_add_check),
              label: Text(s.of('generatePos')),
            ),
          ),
      ],
    );
  }

  Widget _suggestionRow(
    BuildContext context,
    AppStrings s,
    ReplenishmentSuggestion item,
    bool canAdjust,
  ) {
    final row = _rows[item.productId]!;
    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Checkbox(
                  value: row.include,
                  onChanged: (v) => setState(() => row.include = v ?? true),
                ),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(row.name, overflow: TextOverflow.ellipsis),
                      Text(
                        '${item.sku} · stock ${item.currentStock} (min ${item.minStock}) · '
                        'sold ${item.soldQuantity} in lookback',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
                if (canAdjust)
                  IconButton(
                    tooltip: s.of('adjustStock'),
                    icon: const Icon(Icons.add_circle_outline),
                    onPressed: () => _adjust(item),
                  ),
              ],
            ),
            const SizedBox(height: 4),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: row.qty,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(
                      labelText: s.of('adjustDelta'),
                      isDense: true,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextField(
                    controller: row.cost,
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    decoration: InputDecoration(
                      labelText: s.of('unitCost'),
                      isDense: true,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: DropdownButtonFormField<int?>(
                    initialValue: row.supplierId,
                    isExpanded: true,
                    decoration: InputDecoration(
                      labelText: s.of('supplier'),
                      isDense: true,
                    ),
                    items: [
                      ..._suppliers.map(
                        (supplier) => DropdownMenuItem<int?>(
                          value: supplier.id,
                          child: Text(
                            supplier.name,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ),
                      if (row.supplierId != null &&
                          !_suppliers.any((x) => x.id == row.supplierId))
                        DropdownMenuItem<int?>(
                          value: row.supplierId,
                          child: Text(
                            '#${row.supplierId}',
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                    ],
                    onChanged: (v) => row.supplierId = v,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _generate() async {
    final s = ref.read(stringsProvider);
    final items = <Map<String, dynamic>>[];
    for (final entry in _rows.entries) {
      final row = entry.value;
      if (!row.include) continue;
      final qty = int.tryParse(row.qty.text.trim());
      if (qty == null || qty <= 0) continue;
      items.add({
        'product_id': entry.key,
        'quantity_ordered': qty,
        'unit_cost': double.tryParse(row.cost.text.trim()),
        'supplier_id': row.supplierId,
      });
    }
    if (items.isEmpty) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(s.of('noRowsSelected'))));
      return;
    }
    setState(() => _generating = true);
    BatchReplenishmentResult? result;
    try {
      result = await ref
          .read(purchasingRepositoryProvider)
          .batchGenerateFromSuggestions(items: items);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(friendlyError(e, s))));
      }
      return;
    } finally {
      if (mounted) setState(() => _generating = false);
    }
    if (!mounted) return;
    final res = result;
    await showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(s.of('generatePos')),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              s.of(
                'generatedPos',
                args: {'count': '${res.purchaseOrders.length}'},
              ),
            ),
            if (res.skipped.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                s.of('skippedProducts'),
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              for (final skip in res.skipped)
                Text('• ${_productName(skip.productId)}: ${skip.reason}'),
            ],
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: Text(s.of('ok')),
          ),
        ],
      ),
    );
    if (!mounted) return;
    setState(_reload);
  }

  String _productName(int productId) =>
      _rows[productId]?.name ?? '#$productId';
}

class _SuggestionRow {
  final String name;
  final TextEditingController qty;
  final TextEditingController cost;
  int? supplierId;
  bool include = true;

  _SuggestionRow({
    required this.name,
    required this.qty,
    required this.cost,
    this.supplierId,
  });
}
