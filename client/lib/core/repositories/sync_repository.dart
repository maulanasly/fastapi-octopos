library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api_client.dart';
import '../models.dart';

final syncRepositoryProvider = Provider<SyncRepository>(
  (ref) => SyncRepository(ref.watch(apiClientProvider)),
);

class SyncRepository {
  final ApiClient api;
  SyncRepository(this.api);

  Future<CatalogDelta> catalog({String? since}) async {
    final resp = await api.dio.get<Map<String, dynamic>>(
      '/sync/catalog',
      queryParameters: {'since': ?since},
    );
    return CatalogDelta.fromJson(resp.data!);
  }
}
