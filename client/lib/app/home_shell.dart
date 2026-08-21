/// Authenticated shell: navigation rail + section content.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/api_repositories.dart';
import '../core/auth_controller.dart';
import '../core/localization_controller.dart';
import '../core/route_access.dart';
import '../core/strings.dart';
import 'theme_controller.dart';

class HomeShell extends ConsumerWidget {
  const HomeShell({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    final auth = ref.watch(authControllerProvider);
    // Destinations mirror the router's permission table (core/route_access.dart)
    // so navigation and deep-link guards can never drift apart.
    bool can(String path) => routePermitted(auth, path);

    final destinations = <_Dest>[
      const _Dest(icon: Icons.point_of_sale, label: 'POS', path: '/pos'),
      if (can('/serving'))
        const _Dest(
          icon: Icons.room_service,
          label: 'Serving',
          path: '/serving',
        ),
      if (can('/tracking'))
        const _Dest(
          icon: Icons.route,
          label: 'Tracking',
          path: '/tracking',
        ),
      if (can('/orders'))
        const _Dest(
          icon: Icons.receipt_long,
          label: 'Orders',
          path: '/orders',
        ),
      if (can('/inventory'))
        const _Dest(
          icon: Icons.inventory_2,
          label: 'Inventory',
          path: '/inventory',
        ),
      if (can('/purchasing'))
        const _Dest(
          icon: Icons.shopping_cart_outlined,
          label: 'Purchasing',
          path: '/purchasing',
        ),
      if (can('/products'))
        const _Dest(icon: Icons.edit, label: 'Products', path: '/products'),
      if (can('/customers'))
        const _Dest(icon: Icons.people, label: 'Customers', path: '/customers'),
      if (can('/promotions'))
        const _Dest(
          icon: Icons.percent,
          label: 'Promotions',
          path: '/promotions',
        ),
      if (can('/taxes'))
        const _Dest(
          icon: Icons.receipt_long_outlined,
          label: 'Tax rules',
          path: '/taxes',
        ),
      if (can('/settings'))
        const _Dest(
          icon: Icons.settings_outlined,
          label: 'Settings',
          path: '/settings',
        ),
      if (can('/reports'))
        const _Dest(icon: Icons.bar_chart, label: 'Reports', path: '/reports'),
      if (can('/staff')) const _Dest(icon: Icons.badge, label: 'Staff', path: '/staff'),
      if (can('/admin'))
        const _Dest(
          icon: Icons.admin_panel_settings,
          label: 'Admin',
          path: '/admin',
        ),
    ];

    final currentPath = GoRouterState.of(context).uri.path;
    final selected = destinations.indexWhere((d) => d.path == currentPath);
    final narrow = MediaQuery.sizeOf(context).width < 840;

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
          if (!narrow) ...[
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
          ],
          Expanded(child: child),
        ],
      ),
      bottomNavigationBar: narrow
          ? NavigationBar(
              selectedIndex: selected < 0 ? 0 : selected,
              onDestinationSelected: (index) =>
                  context.go(destinations[index].path),
              destinations: [
                for (final d in destinations)
                  NavigationDestination(
                    icon: Icon(d.icon),
                    label: s.of(_stringKeyForPath(d.path)),
                  ),
              ],
            )
          : null,
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
    case '/serving':
      return 'serving';
    case '/customers':
      return 'customers';
    case '/reports':
      return 'reports';
    case '/orders':
      return 'orders';
    case '/inventory':
      return 'inventory';
    case '/purchasing':
      return 'purchasing';
    case '/promotions':
      return 'promotions';
    case '/taxes':
      return 'taxRules';
    case '/settings':
      return 'localizationSettings';
    case '/admin':
      return 'admin';
    case '/staff':
      return 'staff';
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
