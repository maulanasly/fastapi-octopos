/// Application router with auth-aware redirects and a persistent shell.
library;

import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/auth_controller.dart';
import '../core/models.dart';
import '../core/route_access.dart';
import '../features/admin/admin_screen.dart';
import '../features/auth/login_screen.dart';
import '../features/catalog/products_screen.dart';
import '../features/customers/customers_screen.dart';
import '../features/inventory/inventory_screen.dart';
import '../features/orders/orders_screen.dart';
import '../features/purchasing/purchasing_screen.dart';
import '../features/serving/serving_screen.dart';
import '../features/settings/localization_settings_screen.dart';
import '../features/staff/staff_screen.dart';
import '../features/taxes/taxes_screen.dart';
import '../features/tracking/tracking_screen.dart';
import '../features/tracking/trip_map_screen.dart';
import '../features/drawer/reconcile_screen.dart';
import '../features/help/help_screen.dart';
import '../features/pos/pos_screen.dart';
import '../features/pos/receipt_screen.dart';
import '../features/promotions/promotions_screen.dart';
import '../features/refunds/refund_screen.dart';
import '../features/reports/reports_screen.dart';
import 'home_shell.dart';
import 'nav_notice.dart';
import 'not_found_screen.dart';
import 'splash_screen.dart';

final rootNavigatorKey = GlobalKey<NavigatorState>();
final shellNavigatorKey = GlobalKey<NavigatorState>();

class _AuthListenable extends Listenable {
  _AuthListenable(this._ref) {
    _ref.listen<AuthState>(authControllerProvider, (prev, next) {
      for (final l in _listeners) {
        l();
      }
    });
  }

  final Ref _ref;
  final _listeners = <VoidCallback>{};

  @override
  void addListener(VoidCallback listener) => _listeners.add(listener);

  @override
  void removeListener(VoidCallback listener) => _listeners.remove(listener);
}

final routerProvider = Provider<GoRouter>((ref) {
  final router = GoRouter(
    initialLocation: '/pos',
    refreshListenable: _AuthListenable(ref),
    navigatorKey: rootNavigatorKey,
    errorBuilder: (context, state) =>
        NotFoundScreen(path: state.uri.path.isEmpty ? null : state.uri.path),
    redirect: (context, state) {
      final auth = ref.read(authControllerProvider);
      final signedIn = auth.status == AuthStatus.signedIn;
      final path = state.uri.path;
      final onLogin = path == '/login';
      final onSplash = path == '/splash';
      if (auth.status == AuthStatus.unknown) {
        // Cold start: hold on splash instead of flashing login, and
        // remember any deep link for after the session resolves.
        if (onSplash) return null;
        if (!onLogin) {
          ref.read(pendingRedirectProvider.notifier).save(path);
        }
        return '/splash';
      }
      if (!signedIn && !onLogin) {
        // Remember where the user was headed; they land there after
        // signing in instead of always dumping on POS.
        if (!onSplash) {
          ref.read(pendingRedirectProvider.notifier).save(path);
        }
        return '/login';
      }
      if (signedIn && (onLogin || onSplash)) {
        final target = ref.read(pendingRedirectProvider.notifier).consume();
        if (target != null && target != '/login' && target != '/splash') {
          // The permission gate below still applies on arrival: a stale
          // privileged bookmark degrades to POS with a notice.
          return target;
        }
        return '/pos';
      }
      // Permission gate for deep links; falls back to POS when the
      // signed-in user lacks the route's required permission. The
      // fallback reason is stashed for HomeShell to announce once —
      // redirect itself has no Scaffold context for a SnackBar.
      if (signedIn && !routePermitted(auth, path)) {
        ref.read(navNoticeProvider.notifier).show('forbidden');
        return '/pos';
      }
      return null;
    },
    routes: [
      GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
      GoRoute(
        path: '/splash',
        builder: (context, state) => const SplashScreen(),
      ),
      // Full-screen flows pushed over the shell (root navigator).
      GoRoute(
        path: '/refunds',
        parentNavigatorKey: rootNavigatorKey,
        builder: (context, state) => const RefundScreen(),
      ),
      GoRoute(
        path: '/reconcile',
        parentNavigatorKey: rootNavigatorKey,
        builder: (context, state) => const ReconcileScreen(),
      ),
      // Receipt is receipt-of-record for a settled order: top-level so
      // both POS checkout and orders reprint share one canonical,
      // deep-linkable route. Open to all signed-in roles because the
      // cashier POS flow itself ends here.
      GoRoute(
        path: '/receipt/:orderId',
        parentNavigatorKey: rootNavigatorKey,
        builder: (context, state) {
          final orderId = int.tryParse(
            state.pathParameters['orderId'] ?? '',
          );
          if (orderId == null || orderId <= 0) {
            return NotFoundScreen(path: state.uri.path);
          }
          return ReceiptScreen(
            orderId: orderId,
            from: state.uri.queryParameters['from'],
          );
        },
      ),
      ShellRoute(
        navigatorKey: shellNavigatorKey,
        builder: (context, state, child) => HomeShell(child: child),
        routes: [
          GoRoute(path: '/pos', builder: (context, state) => const PosScreen()),
          GoRoute(
            path: '/products',
            builder: (context, state) => const ProductsScreen(),
          ),
          GoRoute(
            path: '/customers',
            builder: (context, state) => const CustomersScreen(),
          ),
          GoRoute(
            path: '/serving',
            builder: (context, state) => const ServingScreen(),
          ),
          GoRoute(
            path: '/tracking',
            builder: (context, state) => const TrackingScreen(),
          ),
          // Sibling (not nested): opening a trip must not build the
          // tracking list underneath — its polling timer would outlive
          // the page and its content would sit under the map.
          GoRoute(
            path: '/tracking/:orderId',
            builder: (context, state) {
              final raw = state.pathParameters['orderId'];
              final orderId = int.tryParse(raw ?? '');
              if (orderId == null || orderId <= 0) {
                // Invalid deep link (e.g. /tracking/abc) -> honest
                // 404 instead of silently showing the list.
                return NotFoundScreen(path: state.uri.path);
              }
              // `extra` is a convenience hand-off from in-app taps;
              // deep links arrive without it (and never with an
              // unexpected type), so treat it as best-effort.
              final extra = state.extra;
              final trip = extra is TrackedOrder
                  ? extra
                  : TrackedOrder(
                      orderId: orderId,
                      status: '',
                      trackingStatus: 'none',
                    );
              return TripMapScreen(trip: trip);
            },
          ),
          GoRoute(
            path: '/orders',
            builder: (context, state) => const OrdersScreen(),
          ),
          GoRoute(
            path: '/inventory',
            builder: (context, state) => const InventoryScreen(),
          ),
          GoRoute(
            path: '/promotions',
            builder: (context, state) => const PromotionsScreen(),
          ),
          GoRoute(
            path: '/admin',
            builder: (context, state) => const AdminScreen(),
          ),
          GoRoute(
            path: '/staff',
            builder: (context, state) => const StaffScreen(),
          ),
          GoRoute(
            path: '/purchasing',
            builder: (context, state) => const PurchasingScreen(),
          ),
          GoRoute(
            path: '/taxes',
            builder: (context, state) => const TaxesScreen(),
          ),
          GoRoute(
            path: '/settings',
            builder: (context, state) => const LocalizationSettingsScreen(),
          ),
          GoRoute(
            path: '/reports',
            builder: (context, state) => const ReportsScreen(),
          ),
          GoRoute(
            path: '/help',
            builder: (context, state) => const HelpScreen(),
          ),
        ],
      ),
    ],
  );
  ref.onDispose(router.dispose);
  return router;
});
