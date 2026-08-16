/// Authenticated shell: navigation rail + section content.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/auth_controller.dart';
import '../core/config.dart';
import 'theme_controller.dart';

class HomeShell extends ConsumerWidget {
  const HomeShell({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    final canManageProducts = auth.has('products:manage');
    final canViewReports = auth.has('reports:view');

    final destinations = <_Dest>[
      const _Dest(icon: Icons.point_of_sale, label: 'POS', path: '/pos'),
      if (canManageProducts)
        const _Dest(
          icon: Icons.inventory_2,
          label: 'Products',
          path: '/products',
        ),
      const _Dest(icon: Icons.people, label: 'Customers', path: '/customers'),
      if (canViewReports)
        const _Dest(
          icon: Icons.receipt_long,
          label: 'Reports',
          path: '/reports',
        ),
    ];

    final currentPath = GoRouterState.of(context).uri.path;
    final selected = destinations.indexWhere((d) => d.path == currentPath);

    return Scaffold(
      appBar: AppBar(
        title: const Text(AppConfig.appTitle),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: Center(
              child: Text(
                auth.email ?? '',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ),
          ),
          IconButton(
            tooltip: 'Toggle theme',
            icon: Icon(
              ref.watch(themeModeProvider) == ThemeMode.dark
                  ? Icons.light_mode
                  : Icons.dark_mode,
            ),
            onPressed: () => ref.read(themeModeProvider.notifier).toggle(),
          ),
          IconButton(
            tooltip: 'Sign out',
            icon: const Icon(Icons.logout),
            onPressed: () => ref.read(authControllerProvider.notifier).logout(),
          ),
        ],
      ),
      body: Row(
        children: [
          NavigationRail(
            selectedIndex: selected < 0 ? 0 : selected,
            onDestinationSelected: (index) =>
                context.go(destinations[index].path),
            labelType: NavigationRailLabelType.all,
            destinations: [
              for (final d in destinations)
                NavigationRailDestination(
                  icon: Icon(d.icon),
                  label: Text(d.label),
                ),
            ],
          ),
          const VerticalDivider(width: 1),
          Expanded(child: child),
        ],
      ),
    );
  }
}

class _Dest {
  const _Dest({required this.icon, required this.label, required this.path});

  final IconData icon;
  final String label;
  final String path;
}
