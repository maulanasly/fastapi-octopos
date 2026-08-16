/// Authenticated shell: navigation rail + section content.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/api_repositories.dart';
import '../core/auth_controller.dart';
import '../core/localization_controller.dart';
import '../core/strings.dart';
import 'theme_controller.dart';

class HomeShell extends ConsumerWidget {
  const HomeShell({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
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
        title: Text(s.of('appTitle')),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: Center(
              child: Tooltip(
                message: auth.email ?? '',
                child: Text(
                  '${s.of('signedInAs')}: ${auth.displayName ?? ''}',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ),
            ),
          ),
          IconButton(
            tooltip: s.of('toggleTheme'),
            icon: Icon(
              ref.watch(themeModeProvider) == ThemeMode.dark
                  ? Icons.light_mode
                  : Icons.dark_mode,
            ),
            onPressed: () => ref.read(themeModeProvider.notifier).toggle(),
          ),
          const _RegionMenu(),
          IconButton(
            tooltip: s.of('signOut'),
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
                  label: Text(s.of(_stringKeyForPath(d.path))),
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

String _stringKeyForPath(String path) {
  switch (path) {
    case '/products':
      return 'products';
    case '/customers':
      return 'customers';
    case '/reports':
      return 'reports';
    case '/orders':
      return 'orders';
    default:
      return 'pos';
  }
}

/// Region preset picker (Default / US / ID), persisted per user.
class _RegionMenu extends ConsumerWidget {
  const _RegionMenu();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = ref.watch(stringsProvider);
    final regions = ref.watch(regionListProvider).value ?? [];
    final current = ref.watch(localizationControllerProvider).setting;
    final currentCode = current?.countryCode ?? '';

    return PopupMenuButton<String?>(
      tooltip: strings.of('region'),
      icon: const Icon(Icons.language),
      onSelected: (code) {
        ref.read(localizationControllerProvider.notifier).setRegion(code);
      },
      itemBuilder: (context) => [
        PopupMenuItem<String?>(
          value: null,
          child: Text(
            strings.of('regionDefault'),
            style: currentCode.isEmpty
                ? const TextStyle(fontWeight: FontWeight.bold)
                : null,
          ),
        ),
        for (final region in regions)
          PopupMenuItem<String?>(
            value: region.countryCode,
            child: Text(
              '${region.countryCode} · ${region.currency}',
              style: currentCode == region.countryCode
                  ? const TextStyle(fontWeight: FontWeight.bold)
                  : null,
            ),
          ),
      ],
    );
  }
}
