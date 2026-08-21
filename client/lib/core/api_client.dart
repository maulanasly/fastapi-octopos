/// Dio-based API client with bearer injection, silent refresh on 401,
/// and session-expiry callback.
library;

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'auth_controller.dart';
import 'config.dart';
import 'models.dart';
import 'token_store.dart';

final tokenStoreProvider = Provider<TokenStore>((ref) => TokenStore());

final apiClientProvider = Provider<ApiClient>((ref) {
  final store = ref.watch(tokenStoreProvider);
  return ApiClient(
    store: store,
    onSessionExpired: () {
      ref.invalidate(authControllerProvider);
    },
  );
});

/// Thrown by the auth controller when no valid session exists.
class SessionExpired implements Exception {
  final String message;
  SessionExpired([this.message = 'Session expired. Please sign in again.']);
}

/// Simple synchronous session holder shared between the interceptor and
/// the auth controller.
class ApiSession {
  String? accessToken;
  String? refreshToken;
  String? language;
}

class ApiClient {
  final Dio dio;
  final TokenStore store;
  final void Function() onSessionExpired;
  final ApiSession session = ApiSession();

  /// Guards concurrent 401s so only one refresh runs.
  Future<bool>? _refreshing;
  bool _disposed = false;

  ApiClient({required this.store, required this.onSessionExpired})
    : dio = Dio(
        BaseOptions(
          baseUrl: AppConfig.apiBaseUrl,
          connectTimeout: const Duration(seconds: 10),
          receiveTimeout: const Duration(seconds: 30),
          headers: {'Accept': 'application/json'},
        ),
      ) {
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          final token = session.accessToken;
          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          final language = session.language;
          if (language != null && language.isNotEmpty) {
            options.headers['Accept-Language'] = language;
          }
          handler.next(options);
        },
        onError: (error, handler) async {
          final original = error.requestOptions;
          final isAuthCall =
              original.path.endsWith('/auth/token') ||
              original.path.endsWith('/auth/refresh') ||
              original.path.endsWith('/auth/logout');
          if (error.response?.statusCode == 401 && !isAuthCall) {
            try {
              final refreshed = await _refreshToken();
              if (refreshed) {
                original.headers['Authorization'] =
                    'Bearer ${session.accessToken}';
                final retry = await dio.fetch(original);
                return handler.resolve(retry);
              }
            } on DioException catch (e) {
              return handler.reject(e);
            }
            _expire();
            return handler.reject(error);
          }
          handler.next(error);
        },
      ),
    );
  }

  /// Loads tokens from persistent storage into the session.
  Future<void> restore() async {
    session.accessToken = await store.readAccessToken();
    session.refreshToken = await store.readRefreshToken();
  }

  Future<TokenResponse> login(String email, String password) async {
    final resp = await dio.post<Map<String, dynamic>>(
      '/auth/token',
      data: FormData.fromMap({'username': email, 'password': password}),
    );
    final tokens = TokenResponse.fromJson(resp.data!);
    await _storeTokens(tokens);
    return tokens;
  }

  Future<TokenResponse> register(
    String email,
    String password,
    String fullName,
  ) async {
    final resp = await dio.post<Map<String, dynamic>>(
      '/auth/register',
      data: {'email': email, 'password': password, 'full_name': fullName},
    );
    final tokens = TokenResponse.fromJson(resp.data!);
    await _storeTokens(tokens);
    return tokens;
  }

  Future<void> logout() async {
    final refresh = session.refreshToken;
    if (refresh != null) {
      try {
        await dio.post('/auth/logout', data: {'refresh_token': refresh});
      } on DioException {
        // Best-effort: revoke locally even if the server call fails.
      }
    }
    await _clearSession();
  }

  Future<void> _storeTokens(TokenResponse tokens) async {
    session.accessToken = tokens.accessToken;
    session.refreshToken = tokens.refreshToken;
    // A fresh sign-in re-arms the expiry callback: without this reset the
    // first expired session would permanently disable the "session
    // expired" redirect for every later sign-in in the same app run.
    _disposed = false;
    await store.saveTokens(
      accessToken: tokens.accessToken,
      refreshToken: tokens.refreshToken,
    );
  }

  Future<bool> _refreshToken() {
    return _refreshing ??= _doRefresh().whenComplete(() => _refreshing = null);
  }

  Future<bool> _doRefresh() async {
    final refresh = session.refreshToken;
    if (refresh == null || refresh.isEmpty) return false;
    try {
      final resp = await dio.post<Map<String, dynamic>>(
        '/auth/refresh',
        data: {'refresh_token': refresh},
        options: Options(),
      );
      final tokens = TokenResponse.fromJson(resp.data!);
      await _storeTokens(tokens);
      return true;
    } on DioException {
      return false;
    }
  }

  void _expire() {
    if (_disposed) return;
    _disposed = true;
    onSessionExpired();
  }

  Future<void> _clearSession() async {
    session.accessToken = null;
    session.refreshToken = null;
    await store.clear();
  }

  void dispose() {
    _disposed = true;
    dio.close();
  }
}
