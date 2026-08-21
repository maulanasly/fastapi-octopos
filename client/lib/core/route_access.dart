/// Single source of truth for route -> permission mapping.
///
/// Consumed by the router's deep-link guard and by the home shell when
/// building navigation destinations, so the two can never drift.
library;

import 'auth_controller.dart';

/// Access rule for one top-level route segment.
class RouteAccess {
  const RouteAccess(
    this.path, {
    this.anyOf = const {},
    this.superuserOnly = false,
  });

  final String path;

  /// Any-of permission codes that grant access.
  final Set<String> anyOf;

  /// When true, only superusers may open the route.
  final bool superuserOnly;
}

const kRouteAccess = <RouteAccess>[
  RouteAccess('/pos'),
  RouteAccess('/serving', anyOf: {'orders:manage'}),
  RouteAccess('/orders', anyOf: {'orders:manage'}),
  RouteAccess('/tracking', anyOf: {'orders:track'}),
  RouteAccess('/inventory', anyOf: {'inventory:view'}),
  RouteAccess('/purchasing', anyOf: {'purchasing:manage'}),
  RouteAccess('/products', anyOf: {'products:manage'}),
  RouteAccess('/customers', anyOf: {'customers:create', 'customers:manage'}),
  RouteAccess('/promotions', anyOf: {'promotions:manage'}),
  RouteAccess('/taxes', anyOf: {'taxes:manage'}),
  RouteAccess('/settings', anyOf: {'settings:manage'}),
  RouteAccess('/staff', anyOf: {'users:manage'}),
  RouteAccess('/reports', anyOf: {'reports:view'}),
  RouteAccess('/admin', superuserOnly: true),
  RouteAccess('/refunds', anyOf: {'refunds:create'}),
  RouteAccess('/reconcile'),
];

RouteAccess? _accessFor(String path) {
  final segment = path.split('/').where((p) => p.isNotEmpty).firstOrNull ?? '';
  for (final access in kRouteAccess) {
    if (access.path == '/$segment') return access;
  }
  return null;
}

/// Whether [auth] may open the deep link [path]. Unknown paths stay open;
/// the router falls back to /pos when this returns false.
bool routePermitted(AuthState auth, String path) {
  if (auth.isSuperuser) return true;
  final access = _accessFor(path);
  if (access == null) return true;
  if (access.superuserOnly) return false;
  if (access.anyOf.isEmpty) return true;
  return access.anyOf.any(auth.has);
}
