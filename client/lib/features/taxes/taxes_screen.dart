/// Tax rules management (tenant-scoped, taxes:manage).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/errors.dart';
import '../../core/models.dart';
import '../../core/strings.dart';

class TaxesScreen extends ConsumerStatefulWidget {
  const TaxesScreen({super.key});

  @override
  ConsumerState<TaxesScreen> createState() => _TaxesScreenState();
}

class _TaxesScreenState extends ConsumerState<TaxesScreen> {
  late Future<List<TaxRule>> _future;

  @override
  void initState() {
    super.initState();
    _future = ref.read(taxRepositoryProvider).list();
  }

  void _reload() {
    setState(() {
      _future = ref.read(taxRepositoryProvider).list();
    });
  }

  Future<void> _edit({TaxRule? rule}) async {
    final s = ref.read(stringsProvider);
    final name = TextEditingController(text: rule?.name ?? '');
    final rate = TextEditingController(
      text: rule == null ? '' : '${rule.rate}',
    );
    var scope = rule?.taxScope ?? 'order';
    var mode = rule?.taxMode ?? 'exclusive';
    var isActive = rule?.isActive ?? true;

    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: Text(rule == null ? s.of('newTaxRule') : s.of('editTaxRule')),
          content: SizedBox(
            width: 380,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: name,
                  decoration: InputDecoration(
                    labelText: s.of('taxName'),
                    isDense: true,
                  ),
                ),
                TextField(
                  controller: rate,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                    labelText: s.of('taxRate'),
                    suffixText: '%',
                    isDense: true,
                  ),
                ),
                DropdownButtonFormField<String>(
                  initialValue: scope,
                  decoration: InputDecoration(
                    labelText: s.of('taxScope'),
                    isDense: true,
                  ),
                  items: const [
                    DropdownMenuItem(value: 'order', child: Text('order')),
                    DropdownMenuItem(value: 'product', child: Text('product')),
                  ],
                  onChanged: (v) => setDialogState(() => scope = v ?? 'order'),
                ),
                DropdownButtonFormField<String>(
                  initialValue: mode,
                  decoration: InputDecoration(
                    labelText: s.of('taxMode'),
                    isDense: true,
                  ),
                  items: const [
                    DropdownMenuItem(
                      value: 'exclusive',
                      child: Text('exclusive'),
                    ),
                    DropdownMenuItem(value: 'inclusive', child: Text('inclusive')),
                  ],
                  onChanged: (v) => setDialogState(() => mode = v ?? 'exclusive'),
                ),
                SwitchListTile(
                  dense: true,
                  contentPadding: EdgeInsets.zero,
                  title: Text(s.of('staffActive')),
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
        ),
      ),
    );
    if (saved != true) return;
    final parsedRate = double.tryParse(rate.text.trim());
    final body = <String, dynamic>{
      if (name.text.trim().isNotEmpty) 'name': name.text.trim(),
      'rate': ?parsedRate,
      'tax_scope': scope,
      'tax_mode': mode,
      'is_active': isActive,
    };
    try {
      final repo = ref.read(taxRepositoryProvider);
      if (rule == null) {
        await repo.create(body);
      } else {
        await repo.update(rule.id, body);
      }
      _reload();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(friendlyError(e, s))));
      }
    }
  }

  Future<void> _deactivate(TaxRule rule) async {
    final s = ref.read(stringsProvider);
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(s.of('deactivate')),
        content: Text(
          s.of('confirmDeactivateStaff', args: {'name': rule.name}),
        ),
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
    if (ok != true) return;
    try {
      await ref.read(taxRepositoryProvider).deactivate(rule.id);
      _reload();
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
    return Scaffold(
      appBar: AppBar(title: Text(s.of('taxRules'))),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _edit(),
        child: const Icon(Icons.add),
      ),
      body: FutureBuilder<List<TaxRule>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text(friendlyError(snapshot.error!, s)));
          }
          final rules = snapshot.data ?? [];
          if (rules.isEmpty) {
            return Center(child: Text(s.of('noTaxRules')));
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: rules.length,
            separatorBuilder: (_, _) => const Divider(height: 8),
            itemBuilder: (context, i) {
              final rule = rules[i];
              return Card(
                margin: EdgeInsets.zero,
                child: ListTile(
                  leading: const Icon(Icons.percent),
                  title: Text(
                    '${rule.name} · ${rule.rate}%${rule.isActive ? '' : ' (${s.of('staffInactive')})'}',
                  ),
                  subtitle: Text(
                    '${rule.taxScope} · ${rule.taxMode}'
                    '${rule.description != null ? ' · ${rule.description}' : ''}',
                  ),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      IconButton(
                        tooltip: s.of('editTaxRule'),
                        icon: const Icon(Icons.edit_outlined),
                        onPressed: () => _edit(rule: rule),
                      ),
                      if (rule.isActive)
                        IconButton(
                          tooltip: s.of('deactivate'),
                          icon: const Icon(Icons.remove_circle_outline),
                          onPressed: () => _deactivate(rule),
                        ),
                    ],
                  ),
                  onTap: () => _edit(rule: rule),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
