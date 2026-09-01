/// Inventory: stock movements, replenishment suggestions, manual adjust.
library;

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../core/api_repositories.dart';
import '../../core/auth_controller.dart';
import '../../core/dates.dart';
import '../../core/errors.dart';
import '../../core/models.dart';
import '../../core/pagination.dart';
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
  int? _productIdFilter;
  DateTime? _startDate;
  DateTime? _endDate;
  int _movementsLimit = 100;
  final _productIdController = TextEditingController();
  bool _onlyReorder = true;
  List<Supplier> _suppliers = const [];
  final Map<int, _SuggestionRow> _rows = {};
  bool _generating = false;

  @override
  void initState() {
    super.initState();
    _reload();
  }

  @override
  void dispose() {
    _productIdController.dispose();
    for (final r in _rows.values) {
      r.qty.dispose();
      r.cost.dispose();
    }
    super.dispose();
  }

  void _reload() {
    _movements = ref.read(inventoryRepositoryProvider).movements(
          movementType: _typeFilter,
          productId: _productIdFilter,
          startDate: _startDate,
          endDate: _endDate,
          pagination: PaginationParams(limit: _movementsLimit),
        );
    _suggestions = ref
        .read(inventoryRepositoryProvider)
        .suggestions(onlyReorder: _onlyReorder);
    _rows.clear();
    _loadSuppliers();
  }

  bool get _hasActiveMovementFilters =>
      _typeFilter != null || _productIdFilter != null || _startDate != null || _endDate != null;

  void _clearMovementFilters() {
    setState(() {
      _typeFilter = null;
      _productIdFilter = null;
      _startDate = null;
      _endDate = null;
      _movementsLimit = 100;
      _productIdController.clear();
      _reload();
    });
  }

  Future<void> _pickDateRange() async {
    final now = DateTime.now();
    final picked = await showDateRangePicker(
      context: context,
      firstDate: DateTime(now.year - 2),
      lastDate: now,
      initialDateRange: _startDate != null && _endDate != null
          ? DateTimeRange(start: _startDate!, end: _endDate!)
          : null,
    );
    if (picked == null) return;
    setState(() {
      _startDate = picked.start;
      _endDate = picked.end;
      _movementsLimit = 100;
      _reload();
    });
  }

  void _applyProductFilter() {
    final raw = _productIdController.text.trim();
    final pid = int.tryParse(raw);
    setState(() {
      _productIdFilter = pid;
      _movementsLimit = 100;
      _reload();
    });
  }

  Future<void> _pickProduct() async {
    final s = ref.read(stringsProvider);
    final searchCtrl = TextEditingController();
    List<Product> results = [];
    bool searching = false;
    String? error;
    Timer? debounce;

    final selected = await showDialog<int>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setD) => AlertDialog(
          title: Text(s.of('selectProduct')),
          content: SizedBox(
            width: 400,
            height: 360,
            child: Column(
              children: [
                TextField(
                  controller: searchCtrl,
                  decoration: InputDecoration(
                    labelText: 'Search product (name/SKU)',
                    prefixIcon: const Icon(Icons.search, size: 18),
                    isDense: true,
                  ),
                  onChanged: (v) {
                    debounce?.cancel();
                    debounce = Timer(const Duration(milliseconds: 400), () async {
                      final q = v.trim();
                      if (q.isEmpty) {
                        setD(() {
                          results = [];
                          error = null;
                          searching = false;
                        });
                        return;
                      }
                      setD(() {
                        searching = true;
                        error = null;
                      });
                      try {
                        // Use API directly for name search with limit 20 (handles huge catalog)
                        final dio = ref.read(apiClientProvider).dio;
                        final resp = await dio.get<List<dynamic>>(
                          '/products/',
                          queryParameters: {'q': q, 'limit': 20},
                        );
                        final list = resp.data!
                            .map((e) => Product.fromJson(e as Map<String, dynamic>))
                            .toList();
                        if (ctx.mounted) {
                          setD(() {
                            results = list;
                            searching = false;
                          });
                        }
                      } catch (e) {
                        if (ctx.mounted) {
                          setD(() {
                            error = friendlyError(e, s);
                            searching = false;
                          });
                        }
                      }
                    });
                  },
                ),
                const SizedBox(height: 8),
                if (searching) const LinearProgressIndicator(),
                if (error != null)
                  Padding(
                    padding: const EdgeInsets.all(8),
                    child: Text(error!, style: const TextStyle(color: Colors.red)),
                  ),
                Expanded(
                  child: ListView.separated(
                    itemCount: results.length,
                    separatorBuilder: (_, _) => const Divider(height: 1),
                    itemBuilder: (c, i) {
                      final p = results[i];
                      return ListTile(
                        dense: true,
                        title: Text(p.name),
                        subtitle: Text('${p.sku} · ${p.stockQuantity} in stock'),
                        onTap: () => Navigator.of(ctx).pop(p.id),
                      );
                    },
                  ),
                ),
                if (results.isEmpty && !searching && searchCtrl.text.isNotEmpty)
                  const Padding(
                    padding: EdgeInsets.all(8),
                    child: Text('No matches'),
                  ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(),
              child: Text(s.of('cancel')),
            ),
            TextButton(
              onPressed: () {
                _productIdController.clear();
                Navigator.of(ctx).pop(0); // 0 means clear filter
              },
              child: Text(s.of('clear')),
            ),
          ],
        ),
      ),
    );
    debounce?.cancel();
    if (selected == null) return;
    setState(() {
      if (selected == 0) {
        _productIdFilter = null;
        _productIdController.clear();
      } else {
        _productIdFilter = selected;
        _productIdController.text = '$selected';
      }
      _movementsLimit = 100;
      _reload();
    });
  }

  void _loadMoreMovements() {
    setState(() {
      _movementsLimit += 100;
      _reload();
    });
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
      await ref
          .read(inventoryRepositoryProvider)
          .adjustStock(
            productId: suggestion.productId,
            delta: parsed,
            note: note.text.trim().isEmpty ? null : note.text.trim(),
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

  Future<void> _adHocReceipt() async {
    final s = ref.read(stringsProvider);
    final productId = TextEditingController();
    final qty = TextEditingController();
    final note = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(s.of('receive')),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: productId,
              keyboardType: TextInputType.number,
              decoration: InputDecoration(
                labelText: s.of('productId', args: {'id': ''}).replaceAll(' #', ''),
                hintText: 'Product ID',
                isDense: true,
              ),
            ),
            TextField(
              controller: qty,
              keyboardType: TextInputType.number,
              decoration: InputDecoration(
                labelText: s.of('qtyReceived'),
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
    final pid = int.tryParse(productId.text.trim());
    final q = int.tryParse(qty.text.trim());
    if (pid == null || q == null || q <= 0) return;
    try {
      await ref
          .read(inventoryRepositoryProvider)
          .adHocReceipt(
            productId: pid,
            quantity: q,
            note: note.text.trim().isEmpty ? null : note.text.trim(),
          );
      await ref.read(catalogControllerProvider.notifier).refresh();
      if (mounted) setState(_reload);
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(s.of('shiftReconciled'))));
      }
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
            tooltip: s.of('receive'),
            icon: const Icon(Icons.add_box),
            onPressed: _adHocReceipt,
          ),
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
    final hasFilters = _hasActiveMovementFilters;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: [
              _typeChip(s, null, s.of('all')),
              _typeChip(s, 'sale', 'sale'),
              _typeChip(s, 'refund', 'refund'),
              _typeChip(s, 'manual_adjustment', 'manual'),
              _typeChip(s, 'initial_stock', 'initial'),
              _typeChip(s, 'purchase_receipt', 'receipt'),
              _typeChip(s, 'ad_hoc_receipt', 'ad-hoc'),
              _typeChip(s, 'reservation_release', 'release'),
              _typeChip(s, 'order_cancel', 'cancel'),
              if (hasFilters)
                ActionChip(
                  label: Text('${s.of('clear')} ✕'),
                  onPressed: _clearMovementFilters,
                ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              SizedBox(
                width: 90,
                child: TextField(
                  controller: _productIdController,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                    labelText: 'Product ID',
                    hintText: 'ID',
                    isDense: true,
                    suffixIcon: IconButton(
                      icon: const Icon(Icons.search, size: 18),
                      onPressed: _applyProductFilter,
                    ),
                  ),
                  onSubmitted: (_) => _applyProductFilter(),
                ),
              ),
              IconButton(
                tooltip: 'Search product',
                icon: const Icon(Icons.manage_search, size: 18),
                onPressed: _pickProduct,
              ),
              const SizedBox(width: 4),
              OutlinedButton.icon(
                icon: const Icon(Icons.date_range, size: 16),
                label: Text(
                  _startDate == null
                      ? 'Date range'
                      : '${_startDate!.month}/${_startDate!.day} - ${_endDate!.month}/${_endDate!.day}',
                ),
                onPressed: _pickDateRange,
              ),
              if (_startDate != null)
                IconButton(
                  icon: const Icon(Icons.clear, size: 18),
                  tooltip: s.of('clear'),
                  onPressed: () => setState(() {
                    _startDate = null;
                    _endDate = null;
                    _movementsLimit = 100;
                    _reload();
                  }),
                ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _typeChip(AppStrings s, String? value, String label) {
    return ChoiceChip(
      label: Text(label),
      selected: _typeFilter == value,
      onSelected: (_) => setState(() {
        _typeFilter = value;
        _movementsLimit = 100;
        _reload();
      }),
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
          return Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(s.of('noMovements')),
                if (_hasActiveMovementFilters)
                  TextButton(
                    onPressed: _clearMovementFilters,
                    child: Text(s.of('clear')),
                  ),
              ],
            ),
          );
        }
        final hasMore = movements.length >= _movementsLimit;
        return RefreshIndicator(
          onRefresh: () async => setState(_reload),
          child: Column(
            children: [
              Expanded(
                child: ListView.separated(
                  padding: const EdgeInsets.all(16),
                  itemCount: movements.length,
                  separatorBuilder: (_, _) => const Divider(height: 8),
                  itemBuilder: (context, i) {
                    final m = movements[i];
                    final delta = m.quantityDelta;
                    final productLabel = m.productName != null
                        ? '${m.productName} (${m.productSku ?? m.productId})'
                        : s.of('productId', args: {'id': m.productId});
                    final meta = [
                      if (m.userEmail != null) m.userEmail!,
                      if (m.orderId != null) 'Order #${m.orderId}',
                      if (m.purchaseOrderId != null) 'PO #${m.purchaseOrderId}',
                      if (m.refundId != null) 'Refund #${m.refundId}',
                    ].join(' · ');
                    return ListTile(
                      leading: Icon(
                        delta >= 0
                            ? Icons.add_box_outlined
                            : Icons.remove_circle_outline,
                        color: delta >= 0 ? Colors.green : Colors.red,
                      ),
                      title: Text('$productLabel · ${m.movementType}'),
                      subtitle: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '${formatDateTimeIso(m.createdAt)}'
                            '${m.note != null ? ' — ${m.note}' : ''}',
                          ),
                          if (meta.isNotEmpty)
                            Text(meta, style: Theme.of(context).textTheme.bodySmall),
                        ],
                      ),
                      trailing: Text(
                        '${m.quantityBefore} → ${m.quantityAfter} (${delta >= 0 ? '+' : ''}$delta)',
                      ),
                    );
                  },
                ),
              ),
              if (hasMore)
                Padding(
                  padding: const EdgeInsets.all(8),
                  child: OutlinedButton.icon(
                    icon: const Icon(Icons.expand_more, size: 18),
                    label: Text('Load more (${movements.length} shown)'),
                    onPressed: _loadMoreMovements,
                  ),
                ),
            ],
          ),
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
            Text(s.of('onlyReorderNeeded')),
          ],
        ),
        Expanded(
          child: RefreshIndicator(
            onRefresh: () async => setState(_reload),
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
                  return ListView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    children: [Center(child: Text(s.of('noSuggestions')))],
                  );
                }
                return ListView.separated(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.all(16),
                  itemCount: suggestions.length,
                  separatorBuilder: (_, _) => const Divider(height: 8),
                  itemBuilder: (context, i) =>
                      _suggestionRow(context, s, suggestions[i], canAdjust),
                );
              },
            ),
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
