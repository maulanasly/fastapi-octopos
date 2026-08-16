/// Thin repositories over the Dio client, one per backend module.
library;

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
final categoryColorPaletteProvider =
    FutureProvider<List<String>>((ref) async {
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

final localizationRepositoryProvider = Provider<LocalizationRepository>(
  (ref) => LocalizationRepository(ref.watch(apiClientProvider)),
);

const _uuid = Uuid();

/// Supported regional presets (fetched once).
final regionListProvider = FutureProvider<List<LocalizationRegion>>((ref) {
  return ref.watch(localizationRepositoryProvider).regions();
});

String newIdempotencyKey() => _uuid.v4();

/// Idempotency-aware post helper: every mutating request carries a fresh
/// idempotency key so retries (offline reconnect, user double-tap) never
/// create duplicates on the backend.
Map<String, dynamic> _withKey(Map<String, dynamic> body, {String? key}) => {
  ...body,
  if (key != null) 'idempotency_key': key,
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
        if (color != null) 'color': color,
      },
    );
    return Category.fromJson(resp.data!);
  }

  /// Curated category color palette (single source of truth with the admin).
  Future<List<String>> categoryColorPalette() async {
    final resp =
        await api.dio.get<List<dynamic>>('/products/categories/colors');
    return resp.data!.cast<String>();
  }

  /// Sets (or clears, with null) a category's display color.
  Future<Category> updateCategoryColor(int categoryId, String? color) async {
    final resp = await api.dio.put<Map<String, dynamic>>(
      '/products/categories/$categoryId',
      data: {
        if (color != null) 'color': color,
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
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/orders/',
      data: _withKey({
        'items': items,
        if (customerId != null) 'customer_id': customerId,
        if (promotionCode != null && promotionCode.isNotEmpty)
          'promotion_code': promotionCode,
        if (redeemPoints > 0) 'redeem_points': redeemPoints,
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
        if (paymentMethod != null) 'payment_method': paymentMethod,
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
        if (notes != null) 'notes': notes,
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
        if (email != null) 'email': email,
        if (phone != null) 'phone': phone,
      },
    );
    return Customer.fromJson(resp.data!);
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

  Future<SalesSummary> sales() async {
    final resp = await api.dio.get<Map<String, dynamic>>('/reports/sales');
    return SalesSummary.fromJson(resp.data!);
  }

  Future<List<Product>> lowStock() async {
    final resp = await api.dio.get<List<dynamic>>('/reports/low-stock');
    return resp.data!
        .map((e) => Product.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<ShiftReport> shiftReport(int reconciliationId) async {
    final resp = await api.dio.get<Map<String, dynamic>>(
      '/reports/shift/$reconciliationId',
    );
    return ShiftReport.fromJson(resp.data!);
  }
}

class SyncRepository {
  final ApiClient api;
  SyncRepository(this.api);

  Future<CatalogDelta> catalog({String? since}) async {
    final resp = await api.dio.get<Map<String, dynamic>>(
      '/sync/catalog',
      queryParameters: {if (since != null) 'since': since},
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
