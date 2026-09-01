library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api_client.dart';
import '../models.dart';

final promotionRepositoryProvider = Provider<PromotionRepository>(
  (ref) => PromotionRepository(ref.watch(apiClientProvider)),
);

class PromotionRepository {
  final ApiClient api;
  PromotionRepository(this.api);

  Future<List<Promotion>> list() async {
    final resp = await api.dio.get<List<dynamic>>('/promotions/');
    return resp.data!
        .map((e) => Promotion.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Promotion> create(Map<String, dynamic> body) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/promotions/',
      data: body,
    );
    return Promotion.fromJson(resp.data!);
  }

  Future<Promotion> update(int id, Map<String, dynamic> body) async {
    final resp = await api.dio.put<Map<String, dynamic>>(
      '/promotions/$id',
      data: body,
    );
    return Promotion.fromJson(resp.data!);
  }

  Future<void> deactivate(int id) async {
    await api.dio.delete('/promotions/$id');
  }
}
