/// Token persistence.
///
/// Native platforms use flutter_secure_storage; on web it falls back to
/// shared_preferences (localStorage) because the secure-storage web
/// backend is experimental. Token storage on web is thus best-effort and
/// sessions may not survive a browser restart.
library;

import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

class TokenStore {
  static const _accessKey = 'octopos_access_token';
  static const _refreshKey = 'octopos_refresh_token';

  final _secure = const FlutterSecureStorage();

  Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
  }) async {
    if (kIsWeb) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_accessKey, accessToken);
      await prefs.setString(_refreshKey, refreshToken);
    } else {
      await _secure.write(key: _accessKey, value: accessToken);
      await _secure.write(key: _refreshKey, value: refreshToken);
    }
  }

  Future<String?> readAccessToken() async {
    if (kIsWeb) {
      final prefs = await SharedPreferences.getInstance();
      return prefs.getString(_accessKey);
    }
    return _secure.read(key: _accessKey);
  }

  Future<String?> readRefreshToken() async {
    if (kIsWeb) {
      final prefs = await SharedPreferences.getInstance();
      return prefs.getString(_refreshKey);
    }
    return _secure.read(key: _refreshKey);
  }

  Future<void> clear() async {
    if (kIsWeb) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_accessKey);
      await prefs.remove(_refreshKey);
    } else {
      await _secure.delete(key: _accessKey);
      await _secure.delete(key: _refreshKey);
    }
  }
}
