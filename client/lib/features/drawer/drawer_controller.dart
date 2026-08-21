/// Drawer session state: the cashier must open a drawer before selling.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/auth_controller.dart';
import '../../core/errors.dart';
import '../../core/models.dart';
import '../../core/strings.dart';

class DrawerState {
  final DrawerSession? session;
  final bool loading;
  final String? error;

  const DrawerState({this.session, this.loading = false, this.error});

  DrawerState copyWith({
    DrawerSession? session,
    bool? loading,
    String? error,
  }) => DrawerState(
    session: session ?? this.session,
    loading: loading ?? this.loading,
    error: error,
  );
}

class DrawerController extends Notifier<DrawerState> {
  @override
  DrawerState build() {
    // A drawer session belongs to the signed-in user; sign-out drops it.
    ref.listen<AuthState>(authControllerProvider, (prev, next) {
      if (prev?.status == AuthStatus.signedIn &&
          next.status == AuthStatus.signedOut) {
        state = const DrawerState();
      }
    });
    _load();
    return const DrawerState(loading: true);
  }

  Future<void> _load() async {
    try {
      final session = await ref.read(drawerRepositoryProvider).active();
      state = DrawerState(session: session);
    } catch (e) {
      state = DrawerState(
        error: friendlyError(e, ref.read(stringsProvider)),
      );
    }
  }

  Future<void> open({required int startingCashCents}) async {
    state = DrawerState(loading: true);
    try {
      final session = await ref
          .read(drawerRepositoryProvider)
          .open(startingCashCents: startingCashCents);
      state = DrawerState(session: session);
    } catch (e) {
      state = DrawerState(
        error: friendlyError(e, ref.read(stringsProvider)),
      );
      rethrow;
    }
  }

  Future<ShiftReconciliation> reconcile({
    required int countedCashCents,
    int? countedNonCashCents,
    String? notes,
  }) async {
    final session = state.session;
    if (session == null) {
      throw StateError('No open drawer to reconcile');
    }
    final rec = await ref
        .read(drawerRepositoryProvider)
        .reconcile(
          sessionId: session.id,
          countedCashCents: countedCashCents,
          countedNonCashCents: countedNonCashCents,
          notes: notes,
        );
    state = const DrawerState();
    return rec;
  }
}

final drawerControllerProvider =
    NotifierProvider<DrawerController, DrawerState>(DrawerController.new);
