library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api_client.dart';
import '../models.dart';

final authRepositoryProvider = Provider<AuthRepository>(
  (ref) => AuthRepository(ref.watch(apiClientProvider)),
);

class AuthRepository {
  final ApiClient api;
  AuthRepository(this.api);

  /// Profile of the authenticated user.
  Future<UserProfile> me() async {
    final resp = await api.dio.get<Map<String, dynamic>>('/auth/me');
    return UserProfile.fromJson(resp.data!);
  }
}
