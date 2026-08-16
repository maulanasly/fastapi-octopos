/// Auth session state + login/register/logout orchestration.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'api_client.dart';
import 'api_repositories.dart';
import 'money.dart';

enum AuthStatus { unknown, signedOut, signedIn }

class AuthState {
  final AuthStatus status;
  final String? email;
  final Set<String> permissions;

  const AuthState({
    this.status = AuthStatus.unknown,
    this.email,
    this.permissions = const {},
  });

  bool has(String permission) => permissions.contains(permission);

  AuthState copyWith({
    AuthStatus? status,
    String? email,
    Set<String>? permissions,
  }) => AuthState(
    status: status ?? this.status,
    email: email ?? this.email,
    permissions: permissions ?? this.permissions,
  );
}

class AuthController extends Notifier<AuthState> {
  @override
  AuthState build() {
    _bootstrap();
    return const AuthState();
  }

  Future<void> _bootstrap() async {
    final api = ref.read(apiClientProvider);
    await api.restore();
    final token = api.session.accessToken;
    if (token == null || token.isEmpty) {
      state = const AuthState(status: AuthStatus.signedOut);
      return;
    }
    // Probe the session; a 401 triggers the silent-refresh path and, on
    // failure, onSessionExpired -> invalidate(this) -> signedOut.
    try {
      final perms = await ref.read(rbacRepositoryProvider).myPermissions();
      await _applyLocalization();
      state = AuthState(
        status: AuthStatus.signedIn,
        permissions: perms.toSet(),
      );
    } catch (_) {
      state = const AuthState(status: AuthStatus.signedOut);
    }
  }

  Future<void> login(String email, String password) async {
    final api = ref.read(apiClientProvider);
    await api.login(email, password);
    final perms = await ref.read(rbacRepositoryProvider).myPermissions();
    await _applyLocalization();
    state = AuthState(
      status: AuthStatus.signedIn,
      email: email,
      permissions: perms.toSet(),
    );
  }

  Future<void> register(String email, String password, String fullName) async {
    final api = ref.read(apiClientProvider);
    await api.register(email, password, fullName);
    final perms = await ref.read(rbacRepositoryProvider).myPermissions();
    await _applyLocalization();
    state = AuthState(
      status: AuthStatus.signedIn,
      email: email,
      permissions: perms.toSet(),
    );
  }

  Future<void> logout() async {
    final api = ref.read(apiClientProvider);
    await api.logout();
    configureMoney(currency: 'USD', numberFormat: 'en_US');
    state = const AuthState(status: AuthStatus.signedOut);
  }

  /// Applies the backend display settings (currency, number format) to the
  /// money formatter. Failures keep the current defaults.
  Future<void> _applyLocalization() async {
    try {
      final settings = await ref
          .read(localizationRepositoryProvider)
          .settings();
      configureMoney(
        currency: settings.currency,
        numberFormat: settings.numberFormat,
      );
    } catch (_) {
      // Keep current formatting when the settings cannot be fetched.
    }
  }
}

final authControllerProvider = NotifierProvider<AuthController, AuthState>(
  AuthController.new,
);
