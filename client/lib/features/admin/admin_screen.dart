/// Admin: audit log + RBAC role management (superuser only).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/dates.dart';
import '../../core/errors.dart';
import '../../core/models.dart';
import '../../core/strings.dart';

class AdminScreen extends ConsumerStatefulWidget {
  const AdminScreen({super.key});

  @override
  ConsumerState<AdminScreen> createState() => _AdminScreenState();
}

class _AdminScreenState extends ConsumerState<AdminScreen> {
  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: Text(s.of('admin')),
          bottom: TabBar(
            tabs: [
              Tab(text: s.of('auditLog')),
              Tab(text: s.of('roles')),
            ],
          ),
        ),
        body: TabBarView(children: const [_AuditTab(), _RolesTab()]),
      ),
    );
  }
}

class _AuditTab extends ConsumerStatefulWidget {
  const _AuditTab();

  @override
  ConsumerState<_AuditTab> createState() => _AuditTabState();
}

class _AuditTabState extends ConsumerState<_AuditTab> {
  late Future<List<AuditLogEntry>> _future;
  String? _action;

  @override
  void initState() {
    super.initState();
    _reload();
  }

  void _reload() {
    _future = ref.read(auditRepositoryProvider).logs(action: _action);
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(8),
          child: DropdownButtonFormField<String?>(
            value: _action,
            decoration: InputDecoration(
              labelText: s.of('action'),
              isDense: true,
            ),
            items: [
              DropdownMenuItem<String?>(value: null, child: Text(s.of('all'))),
              for (final action in const [
                'refund.create',
                'drawer.reconcile',
                'product.stock_adjust',
                'admin.stock_adjust',
                'rbac.role_assign',
                'rbac.role_create',
              ])
                DropdownMenuItem<String?>(value: action, child: Text(action)),
            ],
            onChanged: (v) => setState(() {
              _action = v;
              _reload();
            }),
          ),
        ),
        Expanded(
          child: FutureBuilder<List<AuditLogEntry>>(
            future: _future,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snapshot.hasError) {
                return Center(child: Text(friendlyError(snapshot.error!, s)));
              }
              final entries = snapshot.data ?? [];
              if (entries.isEmpty) {
                return Center(child: Text(s.of('noAuditEntries')));
              }
              return ListView.separated(
                padding: const EdgeInsets.all(16),
                itemCount: entries.length,
                separatorBuilder: (_, _) => const Divider(height: 8),
                itemBuilder: (context, i) {
                  final e = entries[i];
                  return ListTile(
                    dense: true,
                    leading: const Icon(Icons.history, size: 20),
                    title: Text('${e.action} · user ${e.userId ?? '-'}'),
                    subtitle: Text(
                      '${formatDateTimeIso(e.createdAt)}'
                      '${e.resourceType != null ? ' · ${e.resourceType}#${e.resourceId ?? '?'}' : ''}'
                      '${e.ipAddress != null ? ' · ${e.ipAddress}' : ''}',
                    ),
                    trailing: e.detailsJson != null
                        ? const Icon(Icons.chevron_right, size: 18)
                        : null,
                    onTap: e.detailsJson == null
                        ? null
                        : () => showDialog<void>(
                            context: context,
                            builder: (ctx) => AlertDialog(
                              title: Text(e.action),
                              content: SingleChildScrollView(
                                child: Text(e.detailsJson!),
                              ),
                              actions: [
                                TextButton(
                                  onPressed: () => Navigator.of(ctx).pop(),
                                  child: Text(s.of('done')),
                                ),
                              ],
                            ),
                          ),
                  );
                },
              );
            },
          ),
        ),
      ],
    );
  }
}

class _RolesTab extends ConsumerStatefulWidget {
  const _RolesTab();

  @override
  ConsumerState<_RolesTab> createState() => _RolesTabState();
}

class _RolesTabState extends ConsumerState<_RolesTab> {
  late Future<List<RoleInfo>> _future;

  @override
  void initState() {
    super.initState();
    _future = ref.read(rbacAdminRepositoryProvider).roles();
  }

  void _reload() {
    setState(() {
      _future = ref.read(rbacAdminRepositoryProvider).roles();
    });
  }

  Future<void> _edit({RoleInfo? role}) async {
    final s = ref.read(stringsProvider);
    final name = TextEditingController(text: role?.name ?? '');
    final description = TextEditingController(text: role?.description ?? '');
    final permissions = await ref
        .read(rbacAdminRepositoryProvider)
        .permissions();
    final selected = (role?.permissions ?? const <String>[]).toSet();
    if (!mounted) return;

    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: Text(role == null ? s.of('newRole') : s.of('editRole')),
          content: SizedBox(
            width: 380,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: name,
                  decoration: InputDecoration(
                    labelText: s.of('roleName'),
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
                const Divider(height: 16),
                Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    s.of('permissions'),
                    style: Theme.of(ctx).textTheme.titleSmall,
                  ),
                ),
                Flexible(
                  child: ListView(
                    shrinkWrap: true,
                    children: [
                      for (final permission in permissions)
                        CheckboxListTile(
                          dense: true,
                          contentPadding: EdgeInsets.zero,
                          controlAffinity: ListTileControlAffinity.leading,
                          title: Text(permission.code),
                          subtitle: permission.description == null
                              ? null
                              : Text(
                                  permission.description!,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                          value: selected.contains(permission.code),
                          onChanged: (v) => setDialogState(() {
                            if (v == true) {
                              selected.add(permission.code);
                            } else {
                              selected.remove(permission.code);
                            }
                          }),
                        ),
                    ],
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
      ),
    );
    if (saved != true) return;
    try {
      final repo = ref.read(rbacAdminRepositoryProvider);
      if (role == null) {
        await repo.createRole(
          name.text.trim(),
          description.text.trim().isEmpty ? null : description.text.trim(),
          selected.toList()..sort(),
        );
      } else {
        await repo.updateRole(role.id, {
          if (name.text.trim().isNotEmpty) 'name': name.text.trim(),
          if (description.text.trim().isNotEmpty)
            'description': description.text.trim(),
          'permission_codes': selected.toList()..sort(),
        });
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

  Future<void> _assign(RoleInfo role) async {
    final s = ref.read(stringsProvider);
    final users = await ref.read(rbacAdminRepositoryProvider).users();
    if (!mounted) return;
    await showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(s.of('assignRoles')),
        content: SizedBox(
          width: 360,
          child: ListView(
            shrinkWrap: true,
            children: [
              for (final user in users)
                ListTile(
                  dense: true,
                  title: Text(user.fullName ?? user.email),
                  subtitle: Text(user.email),
                  trailing: const Icon(Icons.chevron_right, size: 18),
                  onTap: () async {
                    Navigator.of(ctx).pop();
                    await _assignToUser(user, role);
                  },
                ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: Text(s.of('cancel')),
          ),
        ],
      ),
    );
  }

  Future<void> _assignToUser(UserProfile user, RoleInfo role) async {
    final s = ref.read(stringsProvider);
    try {
      await ref.read(rbacAdminRepositoryProvider).assignRoles(user.id, [
        role.id,
      ]);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('${s.of('assignRoles')}: ${role.name}')),
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

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    return Scaffold(
      floatingActionButton: FloatingActionButton(
        onPressed: () => _edit(),
        child: const Icon(Icons.add),
      ),
      body: FutureBuilder<List<RoleInfo>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text(friendlyError(snapshot.error!, s)));
          }
          final roles = snapshot.data ?? [];
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: roles.length,
            separatorBuilder: (_, _) => const Divider(height: 8),
            itemBuilder: (context, i) {
              final role = roles[i];
              return Card(
                margin: EdgeInsets.zero,
                child: ListTile(
                  title: Text(
                    '${role.name}${role.isSystem ? ' (${s.of('systemRole')})' : ''}',
                  ),
                  subtitle: Text(
                    role.description ??
                        '${role.permissions.length} ${s.of('permissions').toLowerCase()}',
                  ),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      IconButton(
                        tooltip: s.of('assignRoles'),
                        icon: const Icon(Icons.group_add_outlined),
                        onPressed: () => _assign(role),
                      ),
                      IconButton(
                        tooltip: s.of('editRole'),
                        icon: const Icon(Icons.edit_outlined),
                        onPressed: () => _edit(role: role),
                      ),
                    ],
                  ),
                  onTap: () => _edit(role: role),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
