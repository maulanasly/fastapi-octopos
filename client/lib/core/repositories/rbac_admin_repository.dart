library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api_client.dart';
import '../models.dart';

final rbacAdminRepositoryProvider = Provider<RbacAdminRepository>(
  (ref) => RbacAdminRepository(ref.watch(apiClientProvider)),
);

class RbacAdminRepository {
  final ApiClient api;
  RbacAdminRepository(this.api);

  Future<List<PermissionInfo>> permissions() async {
    final resp = await api.dio.get<List<dynamic>>('/rbac/permissions');
    return resp.data!
        .map((e) => PermissionInfo.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<RoleInfo>> roles() async {
    final resp = await api.dio.get<List<dynamic>>('/rbac/roles');
    return resp.data!
        .map((e) => RoleInfo.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<RoleInfo> createRole(
    String name,
    String? description,
    List<String> permissionCodes,
  ) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/rbac/roles',
      data: {
        'name': name,
        'description': description,
        'permission_codes': permissionCodes,
      },
    );
    return RoleInfo.fromJson(resp.data!);
  }

  Future<RoleInfo> updateRole(int id, Map<String, dynamic> body) async {
    final resp = await api.dio.put<Map<String, dynamic>>(
      '/rbac/roles/$id',
      data: body,
    );
    return RoleInfo.fromJson(resp.data!);
  }

  Future<List<UserProfile>> users() async {
    final resp = await api.dio.get<List<dynamic>>('/users/');
    return resp.data!
        .map((e) => UserProfile.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> assignRoles(int userId, List<int> roleIds) async {
    await api.dio.post(
      '/rbac/users/$userId/roles',
      data: {'role_ids': roleIds},
    );
  }
}
