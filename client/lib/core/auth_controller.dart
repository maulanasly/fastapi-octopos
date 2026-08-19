/// Auth session state + login/register/logout orchestration.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'api_client.dart';
import 'api_repositories.dart';
import 'money.dart';

enum AuthStatus { unknown, signedOut, signedIn }

class AuthState {
  final AuthStatus status;
  final int? userId;
  final String? email;
  final String? fullName;
  final Set<String> permissions;
  final bool sessionExpired;
  final bool isSuperuser;

  const AuthState({
    this.status = AuthStatus.unknown,
    this.userId,
    this.email,
    this.fullName,
    this.permissions = const {},
    this.sessionExpired = false,
    this.isSuperuser = false,
  });

  /// Display name for the signed-in user (full name, fallback email).
  String? get displayName => (fullName?.isNotEmpty ?? false) ? fullName : email;

  bool has(String permission) => permissions.contains(permission);

  AuthState copyWith({
    AuthStatus? status,
    int? userId,
    String? email,
    String? fullName,
    Set<String>? permissions,
    bool? sessionExpired,
    bool? isSuperuser,
  }) => AuthState(
    status: status ?? this.status,
    userId: userId ?? this.userId,
    email: email ?? this.email,
    fullName: fullName ?? this.fullName,
    permissions: permissions ?? this.permissions,
    sessionExpired: sessionExpired ?? this.sessionExpired,
    isSuperuser: isSuperuser ?? this.isSuperuser,
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
      await _applyProfile();
      await _applyLocalization();
    } catch (_) {
      state = const AuthState(status: AuthStatus.signedOut);
    }
  }

  /// Loads the profile (id, name, email) and permissions in one pass.
  Future<void> _applyProfile() async {
    final profile = await ref.read(authRepositoryProvider).me();
    final perms = await ref.read(rbacRepositoryProvider).myPermissions();
    state = AuthState(
      status: AuthStatus.signedIn,
      userId: profile.id,
      email: profile.email,
      fullName: profile.fullName,
      permissions: perms.toSet(),
      isSuperuser: profile.isSuperuser,
    );
  }

  Future<void> login(String email, String password) async {
    final api = ref.read(apiClientProvider);
    await api.login(email, password);
    await _applyProfile();
    await _applyLocalization();
  }

  Future<void> register(String email, String password, String fullName) async {
    final api = ref.read(apiClientProvider);
    await api.register(email, password, fullName);
    await _applyProfile();
    await _applyLocalization();
  }

  Future<void> logout() async {
    final api = ref.read(apiClientProvider);
    await api.logout();
    configureMoney(currency: 'USD', numberFormat: 'en_US');
    state = const AuthState(status: AuthStatus.signedOut);
  }

  /// Called when a refresh attempt fails: the session is over and the user
  /// should be told, not silently dumped to the login screen.
  void forceSignOut() {
    configureMoney(currency: 'USD', numberFormat: 'en_US');
    state = const AuthState(status: AuthStatus.signedOut, sessionExpired: true);
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
