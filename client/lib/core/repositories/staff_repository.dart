library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api_client.dart';
import '../models.dart';

final staffRepositoryProvider = Provider<StaffRepository>(
  (ref) => StaffRepository(ref.watch(apiClientProvider)),
);

class StaffRepository {
  final ApiClient api;
  StaffRepository(this.api);

  /// Staff of the current tenant (superusers see all tenants).
  Future<List<UserProfile>> users() async {
    final resp = await api.dio.get<List<dynamic>>('/users/');
    return resp.data!
        .map((e) => UserProfile.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<UserProfile> createUser({
    required String email,
    String? fullName,
    required String password,
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/users/',
      data: {
        'email': email,
        'full_name': ?fullName,
        'password': password,
      },
    );
    return UserProfile.fromJson(resp.data!);
  }

  /// Update a staff member (name, active flag, password reset).
  Future<UserProfile> updateUser(int id, Map<String, dynamic> body) async {
    final resp = await api.dio.put<Map<String, dynamic>>(
      '/users/$id',
      data: body,
    );
    return UserProfile.fromJson(resp.data!);
  }
}
