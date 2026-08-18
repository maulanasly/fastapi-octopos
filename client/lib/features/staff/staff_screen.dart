/// Staff management: list, create, edit, deactivate, and assign roles
/// (per-tenant team administration).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/auth_controller.dart';
import '../../core/errors.dart';
import '../../core/models.dart';
import '../../core/strings.dart';

class StaffScreen extends ConsumerStatefulWidget {
  const StaffScreen({super.key});

  @override
  ConsumerState<StaffScreen> createState() => _StaffScreenState();
}

class _StaffScreenState extends ConsumerState<StaffScreen> {
  late Future<List<UserProfile>> _future;

  @override
  void initState() {
    super.initState();
    _future = ref.read(staffRepositoryProvider).users();
  }

  void _reload() {
    setState(() {
      _future = ref.read(staffRepositoryProvider).users();
    });
  }

  Future<void> _create() async {
    final s = ref.read(stringsProvider);
    final email = TextEditingController();
    final fullName = TextEditingController();
    final password = TextEditingController();

    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(s.of('newStaff')),
        content: SizedBox(
          width: 380,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: email,
                decoration: InputDecoration(
                  labelText: s.of('staffEmail'),
                  isDense: true,
                ),
                keyboardType: TextInputType.emailAddress,
              ),
              TextField(
                controller: fullName,
                decoration: InputDecoration(
                  labelText: s.of('staffFullName'),
                  isDense: true,
                ),
              ),
              TextField(
                controller: password,
                obscureText: true,
                decoration: InputDecoration(
                  labelText: s.of('staffPassword'),
                  helperText: s.of('staffPasswordHint'),
                  isDense: true,
                ),
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
    );
    if (saved != true) return;
    try {
      final created = await ref.read(staffRepositoryProvider).createUser(
        email: email.text.trim(),
        fullName: fullName.text.trim().isEmpty ? null : fullName.text.trim(),
        password: password.text,
      );
      _reload();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('${s.of('staffCreated')}: ${created.email}')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(friendlyError(e, s))));
      }
    }
  }

  Future<void> _edit(UserProfile user) async {
    final s = ref.read(stringsProvider);
    final fullName = TextEditingController(text: user.fullName ?? '');
    final password = TextEditingController();
    var isActive = user.isActive;

    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: Text(s.of('editStaff', args: {'name': user.fullName ?? user.email})),
          content: SizedBox(
            width: 380,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: fullName,
                  decoration: InputDecoration(
                    labelText: s.of('staffFullName'),
                    isDense: true,
                  ),
                ),
                TextField(
                  controller: password,
                  obscureText: true,
                  decoration: InputDecoration(
                    labelText: s.of('resetPassword'),
                    helperText: s.of('resetPasswordHint'),
                    isDense: true,
                  ),
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
    try {
      await ref.read(staffRepositoryProvider).updateUser(user.id, {
        if (fullName.text.trim().isNotEmpty) 'full_name': fullName.text.trim(),
        if (password.text.isNotEmpty) 'password': password.text,
        'is_active': isActive,
      });
      _reload();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(s.of('staffUpdated'))),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(friendlyError(e, s))));
      }
    }
  }

  Future<void> _deactivate(UserProfile user) async {
    final s = ref.read(stringsProvider);
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(s.of('deactivate')),
        content: Text(
          s.of('confirmDeactivateStaff', args: {'name': user.fullName ?? user.email}),
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
    if (confirmed != true) return;
    try {
      await ref.read(staffRepositoryProvider).updateUser(user.id, {
        'is_active': false,
      });
      _reload();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(friendlyError(e, s))));
      }
    }
  }

  Future<void> _assignRoles(UserProfile user) async {
    final s = ref.read(stringsProvider);
    final roles = await ref.read(rbacAdminRepositoryProvider).roles();
    final selected = user.roles.map((name) => name).toSet();
    if (!mounted) return;

    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: Text(s.of('assignRoles')),
          content: SizedBox(
            width: 380,
            child: ListView(
              shrinkWrap: true,
              children: [
                for (final role in roles)
                  CheckboxListTile(
                    dense: true,
                    contentPadding: EdgeInsets.zero,
                    controlAffinity: ListTileControlAffinity.leading,
                    title: Text(role.name),
                    subtitle: role.description == null
                        ? null
                        : Text(
                            role.description!,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                    value: selected.contains(role.name),
                    onChanged: (v) => setDialogState(() {
                      if (v == true) {
                        selected.add(role.name);
                      } else {
                        selected.remove(role.name);
                      }
                    }),
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
    try {
      final roleIds = roles
          .where((r) => selected.contains(r.name))
          .map((r) => r.id)
          .toList();
      await ref.read(rbacAdminRepositoryProvider).assignRoles(user.id, roleIds);
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
    final auth = ref.watch(authControllerProvider);
    final canAssignRoles = auth.has('users:manage_roles');
    final currentUserId = auth.userId;

    return Scaffold(
      appBar: AppBar(title: Text(s.of('staff'))),
      floatingActionButton: FloatingActionButton(
        onPressed: _create,
        child: const Icon(Icons.person_add),
      ),
      body: FutureBuilder<List<UserProfile>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text(friendlyError(snapshot.error!, s)));
          }
          final users = snapshot.data ?? [];
          if (users.isEmpty) {
            return Center(child: Text(s.of('noStaff')));
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: users.length,
            separatorBuilder: (_, _) => const Divider(height: 8),
            itemBuilder: (context, i) {
              final user = users[i];
              return Card(
                margin: EdgeInsets.zero,
                child: ListTile(
                  leading: CircleAvatar(
                    child: Text(
                      (user.fullName ?? user.email)
                          .isEmpty
                          ? '?'
                          : (user.fullName ?? user.email)[0].toUpperCase(),
                    ),
                  ),
                  title: Text(user.fullName ?? user.email),
                  subtitle: Text(
                    '${user.email}${user.roles.isEmpty ? '' : ' · ${s.of('staffRoles', args: {'roles': user.roles.join(', ')})}'}',
                  ),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (canAssignRoles)
                        IconButton(
                          tooltip: s.of('assignRoles'),
                          icon: const Icon(Icons.group_add_outlined),
                          onPressed: () => _assignRoles(user),
                        ),
                      IconButton(
                        tooltip: s.of('editStaff', args: {'name': user.email}),
                        icon: const Icon(Icons.edit_outlined),
                        onPressed: () => _edit(user),
                      ),
                      if (user.isActive && user.id != currentUserId)
                        IconButton(
                          tooltip: s.of('deactivate'),
                          icon: const Icon(Icons.person_off_outlined),
                          onPressed: () => _deactivate(user),
                        ),
                    ],
                  ),
                  onTap: () => _edit(user),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
