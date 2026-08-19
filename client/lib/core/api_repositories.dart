/// Thin repositories over the Dio client, one per backend module.
library;

import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import 'api_client.dart';
import 'models.dart';

final authRepositoryProvider = Provider<AuthRepository>(
  (ref) => AuthRepository(ref.watch(apiClientProvider)),
);

final catalogRepositoryProvider = Provider<CatalogRepository>(
  (ref) => CatalogRepository(ref.watch(apiClientProvider)),
);

/// Curated category color palette from the backend (fallback list for
/// offline use keeps the same tones).
final categoryColorPaletteProvider = FutureProvider<List<String>>((ref) async {
  try {
    return await ref.watch(catalogRepositoryProvider).categoryColorPalette();
  } catch (_) {
    return const [
      '#E8F5E9',
      '#E3F2FD',
      '#FFF3E0',
      '#FCE4EC',
      '#F3E5F5',
      '#E0F2F1',
      '#FFFDE7',
      '#EFEBE9',
    ];
  }
});

final orderRepositoryProvider = Provider<OrderRepository>(
  (ref) => OrderRepository(ref.watch(apiClientProvider)),
);

final drawerRepositoryProvider = Provider<DrawerRepository>(
  (ref) => DrawerRepository(ref.watch(apiClientProvider)),
);

final customerRepositoryProvider = Provider<CustomerRepository>(
  (ref) => CustomerRepository(ref.watch(apiClientProvider)),
);

final rbacRepositoryProvider = Provider<RbacRepository>(
  (ref) => RbacRepository(ref.watch(apiClientProvider)),
);

final reportRepositoryProvider = Provider<ReportRepository>(
  (ref) => ReportRepository(ref.watch(apiClientProvider)),
);

final syncRepositoryProvider = Provider<SyncRepository>(
  (ref) => SyncRepository(ref.watch(apiClientProvider)),
);

final inventoryRepositoryProvider = Provider<InventoryRepository>(
  (ref) => InventoryRepository(ref.watch(apiClientProvider)),
);

final promotionRepositoryProvider = Provider<PromotionRepository>(
  (ref) => PromotionRepository(ref.watch(apiClientProvider)),
);

final auditRepositoryProvider = Provider<AuditRepository>(
  (ref) => AuditRepository(ref.watch(apiClientProvider)),
);

final rbacAdminRepositoryProvider = Provider<RbacAdminRepository>(
  (ref) => RbacAdminRepository(ref.watch(apiClientProvider)),
);

final localizationRepositoryProvider = Provider<LocalizationRepository>(
  (ref) => LocalizationRepository(ref.watch(apiClientProvider)),
);

final staffRepositoryProvider = Provider<StaffRepository>(
  (ref) => StaffRepository(ref.watch(apiClientProvider)),
);

final purchasingRepositoryProvider = Provider<PurchasingRepository>(
  (ref) => PurchasingRepository(ref.watch(apiClientProvider)),
);

final taxRepositoryProvider = Provider<TaxRepository>(
  (ref) => TaxRepository(ref.watch(apiClientProvider)),
);

const _uuid = Uuid();

/// Supported regional presets (fetched once).
final regionListProvider = FutureProvider<List<LocalizationRegion>>((ref) {
  return ref.watch(localizationRepositoryProvider).regions();
});

/// Supported values for tenant localization settings (fetched once).
final localizationOptionsProvider = FutureProvider<LocalizationOptions>((ref) {
  return ref.watch(localizationRepositoryProvider).options();
});

String newIdempotencyKey() => _uuid.v4();

/// Idempotency-aware post helper: every mutating request carries a fresh
/// idempotency key so retries (offline reconnect, user double-tap) never
/// create duplicates on the backend.
Map<String, dynamic> _withKey(Map<String, dynamic> body, {String? key}) => {
  ...body,
  'idempotency_key': ?key,
};

class AuthRepository {
  final ApiClient api;
  AuthRepository(this.api);

  /// Profile of the authenticated user.
  Future<UserProfile> me() async {
    final resp = await api.dio.get<Map<String, dynamic>>('/auth/me');
    return UserProfile.fromJson(resp.data!);
  }
}

class CatalogRepository {
  final ApiClient api;
  CatalogRepository(this.api);

  Future<List<Category>> categories() async {
    final resp = await api.dio.get<List<dynamic>>('/products/categories');
    return resp.data!
        .map((e) => Category.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<Product>> products() async {
    final resp = await api.dio.get<List<dynamic>>(
      '/products/',
      queryParameters: {'limit': 500},
    );
    return resp.data!
        .map((e) => Product.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Semantic catalog search over product embeddings (pgvector).
  Future<List<Product>> searchProducts(String query) async {
    final resp = await api.dio.get<List<dynamic>>(
      '/products/search',
      queryParameters: {'q': query},
    );
    return resp.data!
        .map((e) => Product.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Category> createCategory(
    String name,
    String? description, {
    String? color,
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/products/categories',
      data: {
        'name': name,
        'description': description,
        'color': ?color,
      },
    );
    return Category.fromJson(resp.data!);
  }

  /// Curated category color palette (single source of truth with the admin).
  Future<List<String>> categoryColorPalette() async {
    final resp = await api.dio.get<List<dynamic>>(
      '/products/categories/colors',
    );
    return resp.data!.cast<String>();
  }

  /// Sets (or clears, with null) a category's display color.
  Future<Category> updateCategoryColor(int categoryId, String? color) async {
    final resp = await api.dio.put<Map<String, dynamic>>(
      '/products/categories/$categoryId',
      data: {
        'color': ?color,
        if (color == null) 'color': null,
      },
    );
    return Category.fromJson(resp.data!);
  }

  Future<Product> createProduct(Map<String, dynamic> body) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/products/',
      data: body,
    );
    return Product.fromJson(resp.data!);
  }

  Future<Product> updateProduct(int id, Map<String, dynamic> body) async {
    final resp = await api.dio.put<Map<String, dynamic>>(
      '/products/$id/',
      data: body,
    );
    return Product.fromJson(resp.data!);
  }

  /// Uploads a product photo (multipart). Returns the updated product.
  Future<Product> uploadImage(
    int productId,
    Uint8List bytes,
    String filename,
  ) async {
    final form = FormData.fromMap({
      'file': MultipartFile.fromBytes(
        bytes,
        filename: filename,
        contentType: DioMediaType.parse(_mediaTypeFor(filename)),
      ),
    });
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/products/$productId/image',
      data: form,
    );
    return Product.fromJson(resp.data!);
  }

  /// Removes the product photo.
  Future<Product> deleteImage(int productId) async {
    final resp = await api.dio.delete<Map<String, dynamic>>(
      '/products/$productId/image',
    );
    return Product.fromJson(resp.data!);
  }

  static String _mediaTypeFor(String filename) {
    final lower = filename.toLowerCase();
    if (lower.endsWith('.png')) return 'image/png';
    if (lower.endsWith('.webp')) return 'image/webp';
    return 'image/jpeg';
  }
}

class OrderRepository {
  final ApiClient api;
  OrderRepository(this.api);

  Future<Order> createOrder({
    required List<Map<String, dynamic>> items,
    int? customerId,
    String? promotionCode,
    int redeemPoints = 0,
    String? idempotencyKey,
    String? destinationAddress,
    double? destinationLat,
    double? destinationLng,
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/orders/',
      data: _withKey({
        'items': items,
        'customer_id': ?customerId,
        if (promotionCode != null && promotionCode.isNotEmpty)
          'promotion_code': promotionCode,
        if (redeemPoints > 0) 'redeem_points': redeemPoints,
        if (destinationAddress != null && destinationAddress.isNotEmpty)
          'destination_address': destinationAddress,
        'destination_lat': ?destinationLat,
        'destination_lng': ?destinationLng,
      }, key: idempotencyKey ?? newIdempotencyKey()),
    );
    return Order.fromJson(resp.data!);
  }

  /// Adds a payment to an order. The backend responds with the created
  /// [PaymentLine] (not the whole order).
  Future<PaymentLine> addPayment({
    required int orderId,
    required String method,
    required int amountCents,
    String? idempotencyKey,
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/orders/$orderId/payments',
      data: _withKey({
        'payment_method': method,
        'amount': amountCents / 100,
      }, key: idempotencyKey ?? newIdempotencyKey()),
    );
    return PaymentLine.fromJson(resp.data!);
  }

  Future<Order> addSplitPayments({
    required int orderId,
    required List<Map<String, String>> payments,
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/orders/$orderId/payments/split',
      data: {'payments': payments},
    );
    return Order.fromJson(resp.data!);
  }

  Future<List<Order>> recentOrders({int limit = 50}) async {
    final resp = await api.dio.get<List<dynamic>>(
      '/orders/',
      queryParameters: {'limit': limit},
    );
    return resp.data!
        .map((e) => Order.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<OrderReceipt> receipt(int orderId) async {
    final resp = await api.dio.get<Map<String, dynamic>>(
      '/orders/$orderId/receipt',
    );
    return OrderReceipt.fromJson(resp.data!);
  }

  Future<Order> cancel(int orderId) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/orders/$orderId/cancel',
    );
    return Order.fromJson(resp.data!);
  }

  Future<List<Order>> servingQueue({String? status}) async {
    final resp = await api.dio.get<List<dynamic>>(
      '/orders/serving/',
      queryParameters: {'status': ?status},
    );
    return resp.data!
        .map((e) => Order.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Order> startServing(int orderId) => _servingTransition(orderId, 'start');

  Future<Order> markReady(int orderId) => _servingTransition(orderId, 'ready');

  Future<Order> markServed(int orderId) => _servingTransition(orderId, 'serve');

  Future<Order> _servingTransition(int orderId, String action) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/orders/serving/$orderId/$action',
    );
    return Order.fromJson(resp.data!);
  }

  /// Server-Sent Events stream of serving transitions and tracking
  /// pings (`{"order_id": int, "serving_status": string}` or
  /// `{"order_id": int, "tracking_status": string, ...}`). Each emitted
  /// map carries the SSE event name under `event` (`serving` | `tracking`).
  /// Errors terminate the stream; callers fall back to polling.
  Stream<Map<String, dynamic>> servingEvents() async* {
    final resp = await api.dio.get<ResponseBody>(
      '/orders/serving/stream',
      options: Options(responseType: ResponseType.stream),
    );
    final body = resp.data!;
    final stream = body.stream;
    final buffer = StringBuffer();
    var currentEvent = '';
    await for (final chunk in stream) {
      final text = String.fromCharCodes(chunk);
      for (final line in text.split('\n')) {
        if (line.startsWith('event: ')) {
          currentEvent = line.substring(7).trim();
        } else if (line.startsWith('data: ')) {
          if (currentEvent == 'serving' || currentEvent == 'tracking') {
            buffer.write(line.substring(6));
          }
        } else if (line.trim().isEmpty) {
          if (buffer.isNotEmpty) {
            final payload = buffer.toString();
            buffer.clear();
            final emittedEvent = currentEvent;
            currentEvent = '';
            try {
              final decoded = jsonDecode(payload) as Map<String, dynamic>;
              yield {...decoded, 'event': emittedEvent};
            } on FormatException {
              // ignore malformed frames
            }
          }
        }
      }
    }
  }

  /// Active tracked orders for the tenant with latest positions.
  Future<List<TrackedOrder>> activeTracking() async {
    final resp = await api.dio.get<List<dynamic>>('/orders/tracking/');
    return (resp.data!)
        .map((e) => TrackedOrder.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Advance tracking: assigned -> en_route -> on_site (strict).
  Future<Order> trackingStatus({
    required int orderId,
    required String status,
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/orders/tracking/$orderId/status',
      data: {'status': status},
    );
    return Order.fromJson(resp.data!);
  }

  /// Append a position ping for a tracked order.
  Future<Map<String, dynamic>> reportLocation({
    required int orderId,
    required double lat,
    required double lng,
    String source = 'gps',
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/orders/tracking/$orderId/location',
      data: {'lat': lat, 'lng': lng, 'source': source},
    );
    return resp.data!;
  }

  /// Orders with destinations within [radiusKm] of a point (nearest first).
  Future<List<Map<String, dynamic>>> nearestTracking({
    required double lat,
    required double lng,
    double radiusKm = 10,
  }) async {
    final resp = await api.dio.get<List<dynamic>>(
      '/orders/tracking/nearest',
      queryParameters: {'lat': lat, 'lng': lng, 'radius_km': radiusKm},
    );
    return resp.data!.map((e) => e as Map<String, dynamic>).toList();
  }

  Future<Refund> createRefund({
    required int orderId,
    required List<Map<String, dynamic>> items,
    String? reason,
    String? paymentMethod,
    String? idempotencyKey,
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/refunds/',
      data: _withKey({
        'order_id': orderId,
        'items': items,
        if (reason != null && reason.isNotEmpty) 'reason': reason,
        'payment_method': ?paymentMethod,
      }, key: idempotencyKey ?? newIdempotencyKey()),
    );
    return Refund.fromJson(resp.data!);
  }
}

class DrawerRepository {
  final ApiClient api;
  DrawerRepository(this.api);

  Future<DrawerSession> open({required int startingCashCents}) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/drawers/open',
      data: {'starting_cash': startingCashCents / 100},
    );
    return DrawerSession.fromJson(resp.data!);
  }

  /// Returns null when no active drawer exists (backend 404).
  Future<DrawerSession?> active() async {
    try {
      final resp = await api.dio.get<Map<String, dynamic>>('/drawers/active');
      return DrawerSession.fromJson(resp.data!);
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return null;
      rethrow;
    }
  }

  Future<ShiftReconciliation> reconcile({
    required int sessionId,
    required int countedCashCents,
    int? countedNonCashCents,
    String? notes,
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/drawers/reconcile/$sessionId',
      data: {
        'counted_cash': countedCashCents / 100,
        if (countedNonCashCents != null)
          'counted_non_cash': countedNonCashCents / 100,
        'notes': ?notes,
      },
    );
    return ShiftReconciliation.fromJson(resp.data!);
  }
}

class CustomerRepository {
  final ApiClient api;
  CustomerRepository(this.api);

  Future<List<Customer>> list() async {
    final resp = await api.dio.get<List<dynamic>>('/customers/');
    return resp.data!
        .map((e) => Customer.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Customer> create({
    required String name,
    String? email,
    String? phone,
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/customers/',
      data: {
        'name': name,
        'email': ?email,
        'phone': ?phone,
      },
    );
    return Customer.fromJson(resp.data!);
  }

  Future<Customer> update(int id, Map<String, dynamic> body) async {
    final resp = await api.dio.put<Map<String, dynamic>>(
      '/customers/$id',
      data: body,
    );
    return Customer.fromJson(resp.data!);
  }

  Future<void> deactivate(int id) async {
    await api.dio.delete('/customers/$id');
  }
}

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

class ReportRepository {
  final ApiClient api;
  ReportRepository(this.api);

  Future<SalesSummary> sales({String? startDate, String? endDate}) async {
    final resp = await api.dio.get<Map<String, dynamic>>(
      '/reports/sales',
      queryParameters: {'start_date': ?startDate, 'end_date': ?endDate},
    );
    return SalesSummary.fromJson(resp.data!);
  }

  Future<List<TopProductItem>> topProducts({
    String? startDate,
    String? endDate,
    int limit = 10,
  }) async {
    final resp = await api.dio.get<List<dynamic>>(
      '/reports/top-products',
      queryParameters: {
        'start_date': ?startDate,
        'end_date': ?endDate,
        'limit': limit,
      },
    );
    return resp.data!
        .map((e) => TopProductItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<CategorySalesItem>> categorySales({
    String? startDate,
    String? endDate,
  }) async {
    final resp = await api.dio.get<List<dynamic>>(
      '/reports/categories',
      queryParameters: {'start_date': ?startDate, 'end_date': ?endDate},
    );
    return resp.data!
        .map((e) => CategorySalesItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<Product>> lowStock() async {
    final resp = await api.dio.get<List<dynamic>>('/reports/low-stock');
    return resp.data!
        .map((e) => Product.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<DailyShiftItem>> shifts() async {
    final resp = await api.dio.get<List<dynamic>>('/reports/shifts');
    return resp.data!
        .map((e) => DailyShiftItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<DailyCloseTotals> dailyClose() async {
    final resp = await api.dio.get<Map<String, dynamic>>(
      '/reports/daily-close',
    );
    return DailyCloseTotals.fromJson(
      (resp.data!['totals'] as Map<String, dynamic>),
    );
  }

  Future<ShiftReport> shiftReport(int reconciliationId) async {
    final resp = await api.dio.get<Map<String, dynamic>>(
      '/reports/shift/$reconciliationId',
    );
    return ShiftReport.fromJson(resp.data!);
  }
}

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

class LocalizationRepository {
  final ApiClient api;
  LocalizationRepository(this.api);

  /// Global (admin-managed) localization settings.
  Future<LocalizationSetting> settings() async {
    final resp = await api.dio.get<Map<String, dynamic>>('/localization/');
    return LocalizationSetting.fromJson(resp.data!);
  }

  /// Update the tenant-level localization settings (settings:manage).
  Future<LocalizationSetting> updateSettings(Map<String, dynamic> body) async {
    final resp = await api.dio.put<Map<String, dynamic>>(
      '/localization/',
      data: body,
    );
    return LocalizationSetting.fromJson(resp.data!);
  }

  /// Supported values for the tenant localization settings (settings:manage).
  Future<LocalizationOptions> options() async {
    final resp = await api.dio.get<Map<String, dynamic>>(
      '/localization/options',
    );
    return LocalizationOptions.fromJson(resp.data!);
  }

  /// Effective per-user localization (region preset or global default).
  Future<LocalizationSetting> me() async {
    final resp = await api.dio.get<Map<String, dynamic>>('/localization/me');
    return LocalizationSetting.fromJson(resp.data!);
  }

  /// Supported regional presets.
  Future<List<LocalizationRegion>> regions() async {
    final resp = await api.dio.get<List<dynamic>>('/localization/regions');
    return resp.data!
        .map((e) => LocalizationRegion.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Switch the caller's region preset (null resets to global default).
  Future<LocalizationSetting> updateRegion(String? region) async {
    final resp = await api.dio.put<Map<String, dynamic>>(
      '/localization/me',
      data: {'region': region},
    );
    return LocalizationSetting.fromJson(resp.data!);
  }
}

class PurchasingRepository {
  final ApiClient api;
  PurchasingRepository(this.api);

  // ---- Suppliers ----

  Future<List<Supplier>> suppliers() async {
    final resp = await api.dio.get<List<dynamic>>('/purchasing/suppliers');
    return resp.data!
        .map((e) => Supplier.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Supplier> createSupplier(Map<String, dynamic> body) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/purchasing/suppliers',
      data: body,
    );
    return Supplier.fromJson(resp.data!);
  }

  Future<Supplier> updateSupplier(int id, Map<String, dynamic> body) async {
    final resp = await api.dio.put<Map<String, dynamic>>(
      '/purchasing/suppliers/$id',
      data: body,
    );
    return Supplier.fromJson(resp.data!);
  }

  // ---- Purchase orders ----

  Future<List<PurchaseOrder>> orders({String? status, int limit = 100}) async {
    final resp = await api.dio.get<List<dynamic>>(
      '/purchasing/orders',
      queryParameters: {'status': ?status, 'limit': limit},
    );
    return resp.data!
        .map((e) => PurchaseOrder.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<PurchaseOrder> createOrder({
    required int supplierId,
    required List<Map<String, dynamic>> items,
    String? notes,
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/purchasing/orders',
      data: {
        'supplier_id': supplierId,
        'items': items,
        'notes': ?notes,
      },
    );
    return PurchaseOrder.fromJson(resp.data!);
  }

  Future<PurchaseOrder> markOrdered(int purchaseOrderId) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/purchasing/orders/$purchaseOrderId/mark-ordered',
    );
    return PurchaseOrder.fromJson(resp.data!);
  }

  Future<PurchaseOrder> submitOrder(
    int purchaseOrderId, {
    String? reviewNote,
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/purchasing/orders/$purchaseOrderId/submit-review',
      data: {'review_note': ?reviewNote},
    );
    return PurchaseOrder.fromJson(resp.data!);
  }

  Future<PurchaseOrder> rejectOrder(
    int purchaseOrderId, {
    String? reviewNote,
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/purchasing/orders/$purchaseOrderId/reject',
      data: {'review_note': ?reviewNote},
    );
    return PurchaseOrder.fromJson(resp.data!);
  }

  Future<PurchaseOrder> cancelOrder(int purchaseOrderId) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/purchasing/orders/$purchaseOrderId/cancel',
    );
    return PurchaseOrder.fromJson(resp.data!);
  }

  Future<PurchaseOrder> receiveItems(
    int purchaseOrderId,
    List<Map<String, dynamic>> items,
  ) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/purchasing/orders/$purchaseOrderId/receive',
      data: {'items': items},
    );
    return PurchaseOrder.fromJson(resp.data!);
  }

  // ---- Purchase invoices ----

  Future<List<PurchaseInvoice>> invoices({
    String? status,
    int limit = 100,
  }) async {
    final resp = await api.dio.get<List<dynamic>>(
      '/purchasing/invoices',
      queryParameters: {'status': ?status, 'limit': limit},
    );
    return resp.data!
        .map((e) => PurchaseInvoice.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<PurchaseInvoice> createInvoice(Map<String, dynamic> body) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/purchasing/invoices',
      data: body,
    );
    return PurchaseInvoice.fromJson(resp.data!);
  }

  Future<PurchaseInvoice> submitInvoice(
    int invoiceId, {
    String? reviewNote,
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/purchasing/invoices/$invoiceId/submit-review',
      data: {'review_note': ?reviewNote},
    );
    return PurchaseInvoice.fromJson(resp.data!);
  }

  Future<PurchaseInvoice> approveInvoice(
    int invoiceId, {
    String? reviewNote,
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/purchasing/invoices/$invoiceId/approve',
      data: {'review_note': ?reviewNote},
    );
    return PurchaseInvoice.fromJson(resp.data!);
  }

  Future<PurchaseInvoice> rejectInvoice(
    int invoiceId, {
    String? reviewNote,
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/purchasing/invoices/$invoiceId/reject',
      data: {'review_note': ?reviewNote},
    );
    return PurchaseInvoice.fromJson(resp.data!);
  }

  // ---- Supplier payments ----

  Future<List<SupplierPayment>> payments({
    String? status,
    int limit = 100,
  }) async {
    final resp = await api.dio.get<List<dynamic>>(
      '/purchasing/payments',
      queryParameters: {'status': ?status, 'limit': limit},
    );
    return resp.data!
        .map((e) => SupplierPayment.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<SupplierPayment> createPayment(Map<String, dynamic> body) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/purchasing/payments',
      data: body,
    );
    return SupplierPayment.fromJson(resp.data!);
  }

  Future<SupplierPayment> submitPayment(
    int paymentId, {
    String? reviewNote,
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/purchasing/payments/$paymentId/submit-review',
      data: {'review_note': ?reviewNote},
    );
    return SupplierPayment.fromJson(resp.data!);
  }

  Future<SupplierPayment> approvePayment(
    int paymentId, {
    String? reviewNote,
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/purchasing/payments/$paymentId/approve',
      data: {'review_note': ?reviewNote},
    );
    return SupplierPayment.fromJson(resp.data!);
  }

  Future<SupplierPayment> rejectPayment(
    int paymentId, {
    String? reviewNote,
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/purchasing/payments/$paymentId/reject',
      data: {'review_note': ?reviewNote},
    );
    return SupplierPayment.fromJson(resp.data!);
  }
}

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
