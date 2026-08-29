library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api_client.dart';
import '../models.dart';

final auditRepositoryProvider = Provider<AuditRepository>(
  (ref) => AuditRepository(ref.watch(apiClientProvider)),
);

class AuditRepository {
  final ApiClient api;
  AuditRepository(this.api);

  Future<List<AuditLogEntry>> logs({String? action, int? userId}) async {
    final resp = await api.dio.get<List<dynamic>>(
      '/audit/logs',
      queryParameters: {
        'action': ?action,
        'user_id': ?userId,
      },
    );
    return resp.data!
        .map((e) => AuditLogEntry.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}
