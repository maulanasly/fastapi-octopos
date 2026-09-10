/// Authenticated shell: navigation rail + section content.
library;

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/api_repositories.dart';
import '../core/auth_controller.dart';
import '../core/app_icons.dart';
import '../core/brand.dart';
import '../core/layout.dart';
import '../core/localization_controller.dart';
import '../core/route_access.dart';
import '../core/strings.dart';
import 'nav_notice.dart';
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
      const _Dest(icon: AppIcons.pos, label: 'POS', path: '/pos'),
      if (can('/serving'))
        const _Dest(
          icon: AppIcons.serving,
          label: 'Serving',
          path: '/serving',
        ),
      if (can('/tracking'))
        const _Dest(
          icon: AppIcons.tracking,
          label: 'Tracking',
          path: '/tracking',
        ),
      if (can('/orders'))
        const _Dest(
          icon: AppIcons.orders,
          label: 'Orders',
          path: '/orders',
        ),
      if (can('/inventory'))
        const _Dest(
          icon: AppIcons.inventory,
          label: 'Inventory',
          path: '/inventory',
        ),
      if (can('/purchasing'))
        const _Dest(
          icon: AppIcons.purchasing,
          label: 'Purchasing',
          path: '/purchasing',
        ),
      if (can('/products'))
        const _Dest(icon: AppIcons.products, label: 'Products', path: '/products'),
      if (can('/customers'))
        const _Dest(icon: AppIcons.customers, label: 'Customers', path: '/customers'),
      if (can('/promotions'))
        const _Dest(
          icon: AppIcons.promotions,
          label: 'Promotions',
          path: '/promotions',
        ),
      if (can('/taxes'))
        const _Dest(
          icon: AppIcons.taxes,
          label: 'Tax rules',
          path: '/taxes',
        ),
      if (can('/settings'))
        const _Dest(
          icon: AppIcons.settings,
          label: 'Settings',
          path: '/settings',
        ),
      if (can('/reports'))
        const _Dest(icon: AppIcons.reports, label: 'Reports', path: '/reports'),
      if (can('/staff')) const _Dest(icon: AppIcons.staff, label: 'Staff', path: '/staff'),
      if (can('/admin'))
        const _Dest(
          icon: AppIcons.admin,
          label: 'Admin',
          path: '/admin',
        ),
    ];

    // Role-based ordering: cashiers use Customers frequently (every sale),
    // while Inventory is daily. Keep main bar optimal per role.
    destinations.sort((a, b) {
      final pa = _priorityFor(a.path, auth);
      final pb = _priorityFor(b.path, auth);
      if (pa != pb) return pa.compareTo(pb);
      return 0;
    });

    final currentPath = GoRouterState.of(context).uri.path;
    final selected = _selectedIndex(destinations, currentPath);
    final narrow = MediaQuery.sizeOf(context).width < 840;

    // One-shot redirect feedback (e.g. permission-denied fallback):
    // announce once, then clear so it never repeats or stacks.
    final notice = ref.watch(navNoticeProvider);
    if (notice != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!context.mounted) return;
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(s.of(notice))));
        ref.read(navNoticeProvider.notifier).clear();
      });
    }

    return Scaffold(
      appBar: AppBar(
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const AppMark(size: 26),
            const SizedBox(width: 8),
            Text(s.of('appTitle')),
          ],
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: AppSpacing.sm),
            child: Center(
              child: Tooltip(
                message: auth.email ?? '',
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 200),
                  child: Text(
                    '${s.of('signedInAs')}: ${auth.displayName ?? ''}',
                    style: Theme.of(context).textTheme.bodySmall,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ),
            ),
          ),
          IconButton(
            tooltip: s.of('toggleTheme'),
            icon: Icon(
              ref.watch(themeModeProvider) == ThemeMode.dark
                  ? AppIcons.lightMode
                  : AppIcons.darkMode,
            ),
            onPressed: () => ref.read(themeModeProvider.notifier).toggle(),
          ),
          const _RegionMenu(),
          if (!narrow)
            IconButton(
              tooltip: s.of('help'),
              icon: const Icon(AppIcons.help),
              // Leaf screen: go (replace) so repeated taps don't
              // stack duplicate Help pages.
              onPressed: () => context.go('/help'),
            ),
          IconButton(
            tooltip: s.of('signOut'),
            icon: const Icon(AppIcons.logout),
            onPressed: () => ref.read(authControllerProvider.notifier).logout(),
          ),
        ],
      ),
      body: Row(
        children: [
          if (!narrow) ...[
            // A superuser can have 14 destinations; the rail's internal
            // column does not scroll, so short windows overflowed. Keep
            // the stretched look on tall screens, scroll on short ones.
            LayoutBuilder(
              builder: (context, box) => SingleChildScrollView(
                child: ConstrainedBox(
                  constraints: BoxConstraints(minHeight: box.maxHeight),
                  child: IntrinsicHeight(
                    child: NavigationRail(
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
                  ),
                ),
              ),
            ),
            const VerticalDivider(width: 1),
          ],
          Expanded(child: child),
        ],
      ),
      bottomNavigationBar: narrow
          ? _bottomNav(context, s, destinations, selected, currentPath)
          : null,
    );
  }

  /// The M3 bar flexes every destination equally, so past a handful they
  /// overflow horizontally on tablet-sized widths. Show the first few and
  /// tuck the rest behind a "More" sheet.
  Widget _bottomNav(
    BuildContext context,
    AppStrings s,
    List<_Dest> destinations,
    int selected,
    String currentPath,
  ) {
    const maxVisible = 4;
    // Unlisted paths (e.g. /help, only reachable via the More sheet)
    // highlight More rather than the first destination.
    final onHelp = currentPath == '/help';
    final current = selected < 0 ? (onHelp ? maxVisible : 0) : selected;
    if (destinations.length <= maxVisible + 1) {
      return NavigationBar(
        selectedIndex: current,
        onDestinationSelected: (i) => context.go(destinations[i].path),
        destinations: [
          for (final d in destinations) _navDestination(d, s),
        ],
      );
    }
    return NavigationBar(
      selectedIndex: current < maxVisible && !onHelp ? current : maxVisible,
      onDestinationSelected: (i) {
        if (i < maxVisible) {
          context.go(destinations[i].path);
        } else {
          unawaited(
            _showMoreSheet(context, s, destinations, maxVisible, currentPath),
          );
        }
      },
      destinations: [
        for (final d in destinations.take(maxVisible)) _navDestination(d, s),
        NavigationDestination(icon: const Icon(AppIcons.menu), label: s.of('more')),
      ],
    );
  }

  NavigationDestination _navDestination(_Dest d, AppStrings s) =>
      NavigationDestination(icon: Icon(d.icon), label: s.of(_stringKeyForPath(d.path)));

  Future<void> _showMoreSheet(
    BuildContext context,
    AppStrings s,
    List<_Dest> destinations,
    int skip,
    String currentPath,
  ) {
    final rest = destinations.skip(skip).toList(growable: false);
    return showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (sheetContext) => SafeArea(
        child: ListView.separated(
          shrinkWrap: true,
          itemCount: rest.length + 1,
          separatorBuilder: (_, _) => const Divider(height: 1),
          itemBuilder: (context, i) {
            if (i < rest.length) {
              final d = rest[i];
              final isCurrent =
                  currentPath == d.path ||
                  currentPath.startsWith('${d.path}/');
              return ListTile(
                leading: Icon(d.icon),
                title: Text(s.of(_stringKeyForPath(d.path))),
                trailing: const Icon(AppIcons.chevronRight),
                selected: isCurrent,
                selectedColor: Theme.of(context).colorScheme.primary,
                onTap: () {
                  Navigator.of(sheetContext).pop();
                  context.go(d.path);
                },
              );
            } else {
              return ListTile(
                leading: const Icon(AppIcons.help),
                title: Text(s.of('help')),
                trailing: const Icon(AppIcons.chevronRight),
                selected: currentPath == '/help',
                selectedColor: Theme.of(context).colorScheme.primary,
                onTap: () {
                  Navigator.of(sheetContext).pop();
                  context.go('/help');
                },
              );
            }
          },
        ),
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

/// Index of the destination matching [path], or -1.
///
/// Exact match wins; otherwise the longest parent prefix wins so
/// sub-routes highlight their section (e.g. `/tracking/123` →
/// Tracking). Unlisted shell paths (e.g. `/help`) stay -1 and let the
/// caller decide the fallback.
int _selectedIndex(List<_Dest> destinations, String path) {
  final exact = destinations.indexWhere((d) => d.path == path);
  if (exact >= 0) return exact;
  var best = -1;
  var bestLen = -1;
  for (var j = 0; j < destinations.length; j++) {
    final p = destinations[j].path;
    if (path.startsWith('$p/') && p.length > bestLen) {
      best = j;
      bestLen = p.length;
    }
  }
  return best;
}

String _stringKeyForPath(String path) {
  switch (path) {
    case '/products':
      return 'products';
    case '/serving':
      return 'serving';
    case '/tracking':
      return 'tracking';
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
    case '/help':
      return 'help';
    default:
      return 'pos';
  }
}

int _priorityFor(String path, AuthState auth) {
  // Cashier: POS, Serving, Orders, Customers, Inventory
  // Manager: POS, Serving, Orders, Purchasing, Products, Inventory, Customers, Promotions, Taxes, Settings, Reports, Staff
  // Admin/superuser: keep original declaration order (return 0 to preserve)
  if (auth.isSuperuser) return 0;
  final isManager = auth.has('purchasing:manage') || auth.has('products:manage');
  if (!isManager) {
    // Cashier ordering
    const order = ['/pos', '/serving', '/orders', '/customers', '/inventory'];
    final idx = order.indexOf(path);
    return idx == -1 ? 99 : idx;
  } else {
    const order = [
      '/pos',
      '/serving',
      '/orders',
      '/purchasing',
      '/products',
      '/inventory',
      '/customers',
      '/promotions',
      '/taxes',
      '/settings',
      '/reports',
      '/staff',
      '/tracking',
      '/admin',
    ];
    final idx = order.indexOf(path);
    return idx == -1 ? 99 : idx;
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
      icon: const Icon(AppIcons.language),
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
