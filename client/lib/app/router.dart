/// Application router with auth-aware redirects and a persistent shell.
library;

import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/auth_controller.dart';
import '../features/admin/admin_screen.dart';
import '../features/auth/login_screen.dart';
import '../features/catalog/products_screen.dart';
import '../features/customers/customers_screen.dart';
import '../features/inventory/inventory_screen.dart';
import '../features/orders/orders_screen.dart';
import '../features/serving/serving_screen.dart';
import '../features/drawer/reconcile_screen.dart';
import '../features/pos/pos_screen.dart';
import '../features/promotions/promotions_screen.dart';
import '../features/refunds/refund_screen.dart';
import '../features/reports/reports_screen.dart';
import 'home_shell.dart';

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
    redirect: (context, state) {
      final auth = ref.read(authControllerProvider);
      final signedIn = auth.status == AuthStatus.signedIn;
      final onLogin = state.uri.path == '/login';
      if (!signedIn && !onLogin) return '/login';
      if (signedIn && onLogin) return '/pos';
      return null;
    },
    routes: [
      GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
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
            path: '/reports',
            builder: (context, state) => const ReportsScreen(),
          ),
        ],
      ),
    ],
  );
  ref.onDispose(router.dispose);
  return router;
});
