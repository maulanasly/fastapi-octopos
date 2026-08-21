/// Promotions management: list, create/edit, deactivate.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/errors.dart';
import '../../core/money.dart';
import '../../core/models.dart';
import '../../core/strings.dart';
import '../pos/catalog_controller.dart';

class PromotionsScreen extends ConsumerStatefulWidget {
  const PromotionsScreen({super.key});

  @override
  ConsumerState<PromotionsScreen> createState() => _PromotionsScreenState();
}

class _PromotionsScreenState extends ConsumerState<PromotionsScreen> {
  late Future<List<Promotion>> _future;

  @override
  void initState() {
    super.initState();
    _future = ref.read(promotionRepositoryProvider).list();
  }

  void _reload() {
    setState(() {
      _future = ref.read(promotionRepositoryProvider).list();
    });
  }

  Future<void> _edit({Promotion? promotion}) async {
    final s = ref.read(stringsProvider);
    final code = TextEditingController(text: promotion?.code ?? '');
    final name = TextEditingController(text: promotion?.name ?? '');
    final description = TextEditingController(
      text: promotion?.description ?? '',
    );
    var discountType = promotion?.discountType ?? 'percentage';
    final value = TextEditingController(
      text: promotion == null
          ? ''
          : centsToApi((promotion.discountValue * 100).round()),
    );
    final minOrder = TextEditingController(
      text: promotion == null
          ? '0'
          : centsToApi((promotion.minOrderAmount * 100).round()),
    );
    final maxDiscountAmount = promotion?.maxDiscountAmount;
    final maxDiscount = TextEditingController(
      text: maxDiscountAmount == null
          ? ''
          : centsToApi((maxDiscountAmount * 100).round()),
    );
    var appliesTo = promotion?.appliesTo ?? 'order';
    var categoryId = promotion?.categoryId;
    var isActive = promotion?.isActive ?? true;
    final usageLimit = TextEditingController(
      text: promotion?.usageLimit?.toString() ?? '',
    );

    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) {
          final categories = ref.read(catalogControllerProvider).categories;
          return AlertDialog(
            title: Text(
              promotion == null ? s.of('newPromotion') : s.of('editPromotion'),
            ),
            content: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(
                    controller: code,
                    decoration: InputDecoration(
                      labelText: s.of('promotionCode'),
                      isDense: true,
                    ),
                  ),
                  TextField(
                    controller: name,
                    decoration: InputDecoration(
                      labelText: s.of('name'),
                      isDense: true,
                    ),
                  ),
                  TextField(
                    controller: description,
                    decoration: InputDecoration(
                      labelText: s.of('description'),
                      isDense: true,
                    ),
                  ),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      s.of('discountType'),
                      style: Theme.of(ctx).textTheme.bodySmall,
                    ),
                  ),
                  SegmentedButton<String>(
                    segments: [
                      ButtonSegment(
                        value: 'percentage',
                        label: Text(s.of('percentage')),
                      ),
                      ButtonSegment(value: 'fixed', label: Text(s.of('fixed'))),
                    ],
                    selected: {discountType},
                    onSelectionChanged: (v) =>
                        setDialogState(() => discountType = v.first),
                  ),
                  TextField(
                    controller: value,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(
                      labelText: s.of('discountValue'),
                      isDense: true,
                    ),
                  ),
                  TextField(
                    controller: minOrder,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(
                      labelText: s.of('minOrder'),
                      isDense: true,
                    ),
                  ),
                  TextField(
                    controller: maxDiscount,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(
                      labelText: s.of('maxDiscount'),
                      isDense: true,
                    ),
                  ),
                  DropdownButtonFormField<String>(
                    initialValue: appliesTo,
                    decoration: InputDecoration(
                      labelText: s.of('appliesTo'),
                      isDense: true,
                    ),
                    items: [
                      for (final value in const [
                        'order',
                        'category',
                        'product',
                      ])
                        DropdownMenuItem(
                          value: value,
                          child: Text(_scopeLabel(s, value)),
                        ),
                    ],
                    onChanged: (v) => setDialogState(() {
                      appliesTo = v ?? 'order';
                      if (appliesTo != 'category') categoryId = null;
                    }),
                  ),
                  if (appliesTo == 'category')
                    DropdownButtonFormField<int>(
                      initialValue: categoryId,
                      decoration: InputDecoration(
                        labelText: s.of('category'),
                        isDense: true,
                      ),
                      items: [
                        for (final c in categories)
                          DropdownMenuItem(value: c.id, child: Text(c.name)),
                      ],
                      onChanged: (v) => setDialogState(() => categoryId = v),
                    ),
                  TextField(
                    controller: usageLimit,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(
                      labelText: s.of('usageLimit'),
                      isDense: true,
                    ),
                  ),
                  SwitchListTile(
                    contentPadding: EdgeInsets.zero,
                    title: Text(s.of('isActive')),
                    value: isActive,
                    onChanged: (v) => setDialogState(() => isActive = v),
                  ),
                ],
              ),
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
          );
        },
      ),
    );

    if (saved != true) return;
    final body = <String, dynamic>{
      'code': code.text.trim(),
      'name': name.text.trim(),
      'discount_type': discountType,
      'discount_value': double.tryParse(value.text) ?? 0,
      'min_order_amount': double.tryParse(minOrder.text) ?? 0,
      'applies_to': appliesTo,
      'is_active': isActive,
      if (description.text.trim().isNotEmpty)
        'description': description.text.trim(),
      if (maxDiscount.text.trim().isNotEmpty)
        'max_discount_amount': double.tryParse(maxDiscount.text),
      if (appliesTo == 'category' && categoryId != null)
        'category_id': categoryId,
      if (usageLimit.text.trim().isNotEmpty)
        'usage_limit': int.tryParse(usageLimit.text),
    };
    try {
      if (promotion == null) {
        await ref.read(promotionRepositoryProvider).create(body);
      } else {
        await ref.read(promotionRepositoryProvider).update(promotion.id, body);
      }
      _reload();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(friendlyError(e, s))));
      }
    }
  }

  Future<void> _deactivate(Promotion promotion) async {
    final s = ref.read(stringsProvider);
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(s.of('deactivate')),
        content: Text(s.of('confirmDeactivate')),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text(s.of('cancel')),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: Text(s.of('deactivate')),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    try {
      await ref.read(promotionRepositoryProvider).deactivate(promotion.id);
      _reload();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(friendlyError(e, s))));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    return Scaffold(
      appBar: AppBar(
        title: Text(s.of('promotions')),
        actions: [
          IconButton(
            tooltip: s.of('promotions'),
            icon: const Icon(Icons.refresh),
            onPressed: _reload,
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _edit(),
        child: const Icon(Icons.add),
      ),
      body: FutureBuilder<List<Promotion>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text(friendlyError(snapshot.error!, s)));
          }
          final promotions = snapshot.data ?? [];
          if (promotions.isEmpty) {
            return Center(child: Text(s.of('noPromotions')));
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: promotions.length,
            separatorBuilder: (_, _) => const Divider(height: 8),
            itemBuilder: (context, i) {
              final p = promotions[i];
              final usage = p.usageLimit == null
                  ? s.of('usageUnlimited', args: {'count': p.usageCount})
                  : s.of(
                      'usage',
                      args: {'count': p.usageCount, 'limit': p.usageLimit!},
                    );
              return Card(
                margin: EdgeInsets.zero,
                child: ListTile(
                  title: Text('${p.code} — ${p.name}'),
                  subtitle: Text(
                    '${p.discountType == 'percentage' ? '${p.discountValue}%' : formatCents((p.discountValue * 100).round())}'
                    ' · ${p.appliesTo} · $usage',
                  ),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (p.isActive)
                        const Icon(Icons.check_circle, color: Colors.green)
                      else
                        const Icon(Icons.pause_circle_outline),
                      IconButton(
                        tooltip: s.of('editPromotion'),
                        icon: const Icon(Icons.edit_outlined),
                        onPressed: () => _edit(promotion: p),
                      ),
                      if (p.isActive)
                        IconButton(
                          tooltip: s.of('deactivate'),
                          icon: const Icon(Icons.remove_circle_outline),
                          onPressed: () => _deactivate(p),
                        ),
                    ],
                  ),
                  onTap: () => _edit(promotion: p),
                ),
              );
            },
          );
        },
      ),
    );
  }
}

/// Localized label for a promotion's applies-to scope.
String _scopeLabel(AppStrings s, String scope) => switch (scope) {
  'category' => s.of('scopeCategory'),
  'product' => s.of('scopeProduct'),
  _ => s.of('scopeOrder'),
};
