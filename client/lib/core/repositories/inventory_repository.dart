library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api_client.dart';
import '../models.dart';
import '../pagination.dart';

final inventoryRepositoryProvider = Provider<InventoryRepository>(
  (ref) => InventoryRepository(ref.watch(apiClientProvider)),
);

class InventoryRepository {
  final ApiClient api;
  InventoryRepository(this.api);

  Future<List<StockMovement>> movements({
    int? productId,
    String? movementType,
    DateTime? startDate,
    DateTime? endDate,
    int? userId,
    int? purchaseOrderId,
    PaginationParams pagination = PaginationParams.inventory,
  }) async {
    final resp = await api.dio.get<List<dynamic>>(
      '/inventory/movements',
      queryParameters: {
        'product_id': ?productId,
        'movement_type': ?movementType,
        'user_id': ?userId,
        'purchase_order_id': ?purchaseOrderId,
        'start_date': ?startDate?.toIso8601String(),
        'end_date': ?endDate?.toIso8601String(),
        ...pagination.toQuery(),
      },
    );
    return resp.data!
        .map((e) => StockMovement.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> adjustStock({
    required int productId,
    required int delta,
    String? note,
  }) async {
    await api.dio.put<Map<String, dynamic>>(
      '/products/$productId',
      data: {
        'stock_delta': delta,
        'stock_note': ?note,
      },
    );
  }

  Future<StockMovement> adHocReceipt({
    required int productId,
    required int quantity,
    double? unitCost,
    int? supplierId,
    String? note,
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/inventory/receipt',
      data: {
        'product_id': productId,
        'quantity': quantity,
        'unit_cost': ?unitCost,
        'supplier_id': ?supplierId,
        'note': ?note,
      },
    );
    return StockMovement.fromJson(resp.data!);
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
