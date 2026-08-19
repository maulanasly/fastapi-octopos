/// Customer list + create.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/auth_controller.dart';
import '../../core/errors.dart';
import '../../core/strings.dart';
import '../../core/models.dart';

class CustomersScreen extends ConsumerStatefulWidget {
  const CustomersScreen({super.key});

  @override
  ConsumerState<CustomersScreen> createState() => _CustomersScreenState();
}

class _CustomersScreenState extends ConsumerState<CustomersScreen> {
  late Future<List<Customer>> _future;

  @override
  void initState() {
    super.initState();
    _future = ref.read(customerRepositoryProvider).list();
  }

  Future<void> _edit(Customer customer) async {
    final s = ref.read(stringsProvider);
    final name = TextEditingController(text: customer.name);
    final email = TextEditingController(text: customer.email ?? '');
    final phone = TextEditingController(text: customer.phone ?? '');
    var isActive = customer.isActive;
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: Text('${s.of('editCustomer')}: ${customer.name}'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: name,
                decoration: InputDecoration(labelText: s.of('name')),
              ),
              TextField(
                controller: email,
                decoration: InputDecoration(labelText: s.of('email')),
              ),
              TextField(
                controller: phone,
                decoration: InputDecoration(labelText: s.of('phone')),
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
    if (ok != true) return;
    try {
      await ref.read(customerRepositoryProvider).update(customer.id, {
        if (name.text.trim().isNotEmpty) 'name': name.text.trim(),
        if (email.text.trim().isNotEmpty) 'email': email.text.trim(),
        if (phone.text.trim().isNotEmpty) 'phone': phone.text.trim(),
        'is_active': isActive,
      });
      setState(() => _future = ref.read(customerRepositoryProvider).list());
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(friendlyError(e, ref.read(stringsProvider)))),
        );
      }
    }
  }

  Future<void> _deactivate(Customer customer) async {
    final s = ref.read(stringsProvider);
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(s.of('deactivate')),
        content: Text(
          s.of('confirmDeactivateStaff', args: {'name': customer.name}),
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
      await ref.read(customerRepositoryProvider).deactivate(customer.id);
      setState(() => _future = ref.read(customerRepositoryProvider).list());
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(friendlyError(e, ref.read(stringsProvider)))),
        );
      }
    }
  }

  Future<void> _create() async {
    final s = ref.read(stringsProvider);
    final name = TextEditingController();
    final email = TextEditingController();
    final phone = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(s.of('newCustomer')),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: name,
              decoration: InputDecoration(labelText: s.of('name')),
            ),
            TextField(
              controller: email,
              decoration: InputDecoration(labelText: s.of('email')),
            ),
            TextField(
              controller: phone,
              decoration: InputDecoration(labelText: s.of('phone')),
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
            child: Text(s.of('create')),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await ref
          .read(customerRepositoryProvider)
          .create(
            name: name.text.trim(),
            email: email.text.trim().isEmpty ? null : email.text.trim(),
            phone: phone.text.trim().isEmpty ? null : phone.text.trim(),
          );
      setState(() => _future = ref.read(customerRepositoryProvider).list());
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(friendlyError(e, ref.read(stringsProvider)))),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    final canManage = ref
        .watch(authControllerProvider)
        .has('customers:manage');
    return Scaffold(
      appBar: AppBar(title: Text(s.of('customers'))),
      floatingActionButton: FloatingActionButton(
        onPressed: _create,
        child: const Icon(Icons.add),
      ),
      body: FutureBuilder<List<Customer>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text('Failed to load:\n${snapshot.error}'));
          }
          final customers = snapshot.data ?? [];
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: customers.length,
            separatorBuilder: (_, _) => const Divider(height: 8),
            itemBuilder: (context, i) {
              final customer = customers[i];
              return ListTile(
                leading: CircleAvatar(
                  child: Text(customer.name.characters.first),
                ),
                title: Text(
                  '${customer.name}${customer.isActive ? '' : ' (${s.of('staffInactive')})'}',
                ),
                subtitle: Text(customer.email ?? customer.phone ?? ''),
                trailing: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text('${customer.pointsBalance} pts'),
                    if (canManage) ...[
                      IconButton(
                        tooltip: s.of('editCustomer'),
                        icon: const Icon(Icons.edit_outlined),
                        onPressed: () => _edit(customer),
                      ),
                      if (customer.isActive)
                        IconButton(
                          tooltip: s.of('deactivate'),
                          icon: const Icon(Icons.person_off_outlined),
                          onPressed: () => _deactivate(customer),
                        ),
                    ],
                  ],
                ),
                onTap: canManage ? () => _edit(customer) : null,
              );
            },
          );
        },
      ),
    );
  }
}
