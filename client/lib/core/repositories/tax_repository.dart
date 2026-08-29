library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api_client.dart';
import '../models.dart';

final taxRepositoryProvider = Provider<TaxRepository>(
  (ref) => TaxRepository(ref.watch(apiClientProvider)),
);

class TaxRepository {
  final ApiClient api;
  TaxRepository(this.api);

  Future<List<TaxRule>> list() async {
    final resp = await api.dio.get<List<dynamic>>('/taxes/');
    return resp.data!
        .map((e) => TaxRule.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<TaxRule> create(Map<String, dynamic> body) async {
    final resp = await api.dio.post<Map<String, dynamic>>('/taxes/', data: body);
    return TaxRule.fromJson(resp.data!);
  }

  Future<TaxRule> update(int id, Map<String, dynamic> body) async {
    final resp = await api.dio.put<Map<String, dynamic>>('/taxes/$id', data: body);
    return TaxRule.fromJson(resp.data!);
  }

  Future<void> deactivate(int id) async {
    await api.dio.delete('/taxes/$id');
  }
}
