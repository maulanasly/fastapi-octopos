library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api_client.dart';
import '../models.dart';

final inventoryRepositoryProvider = Provider<InventoryRepository>(
  (ref) => InventoryRepository(ref.watch(apiClientProvider)),
);

class InventoryRepository {
  final ApiClient api;
  InventoryRepository(this.api);

  Future<List<StockMovement>> movements({
    int? productId,
    String? movementType,
    int limit = 100,
  }) async {
    final resp = await api.dio.get<List<dynamic>>(
      '/inventory/movements',
      queryParameters: {
        'product_id': ?productId,
        'movement_type': ?movementType,
        'limit': limit,
      },
    );
    return resp.data!
        .map((e) => StockMovement.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<ReplenishmentSuggestion>> suggestions({
    int lookbackDays = 30,
    bool onlyReorder = true,
  }) async {
    final resp = await api.dio.get<List<dynamic>>(
      '/inventory/replenishment-suggestions',
      queryParameters: {
        'lookback_days': lookbackDays,
        'only_reorder_needed': onlyReorder,
      },
    );
    return resp.data!
        .map((e) => ReplenishmentSuggestion.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}
