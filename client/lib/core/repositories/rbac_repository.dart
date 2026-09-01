library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api_client.dart';

final rbacRepositoryProvider = Provider<RbacRepository>(
  (ref) => RbacRepository(ref.watch(apiClientProvider)),
);

class RbacRepository {
  final ApiClient api;
  RbacRepository(this.api);

  Future<List<String>> myPermissions() async {
    final resp = await api.dio.get<Map<String, dynamic>>(
      '/rbac/me/permissions',
    );
    return (resp.data!['permissions'] as List? ?? []).cast<String>();
  }
}
