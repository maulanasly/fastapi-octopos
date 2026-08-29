library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api_client.dart';
import '../models.dart';
import '../pagination.dart';

final purchasingRepositoryProvider = Provider<PurchasingRepository>(
  (ref) => PurchasingRepository(ref.watch(apiClientProvider)),
);

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

  Future<List<PurchaseOrder>> orders({String? status, PaginationParams pagination = PaginationParams.purchasing}) async {
    final resp = await api.dio.get<List<dynamic>>(
      '/purchasing/orders',
      queryParameters: {'status': ?status, ...pagination.toQuery()},
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

  Future<BatchReplenishmentResult> batchGenerateFromSuggestions({
    int lookbackDays = 30,
    List<Map<String, dynamic>> items = const [],
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/purchasing/orders/batch-from-replenishment',
      data: {
        'lookback_days': lookbackDays,
        'items': items,
      },
    );
    final data = resp.data!;
    return BatchReplenishmentResult(
      purchaseOrders: (data['purchase_orders'] as List<dynamic>? ?? [])
          .map((e) => PurchaseOrder.fromJson(e as Map<String, dynamic>))
          .toList(),
      skipped: (data['skipped_products'] as List<dynamic>? ?? [])
          .map(
            (e) => SkippedProduct.fromJson(e as Map<String, dynamic>),
          )
          .toList(),
    );
  }

  Future<PurchaseOrder> markOrdered(
    int purchaseOrderId, {
    String? reviewNote,
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/purchasing/orders/$purchaseOrderId/mark-ordered',
      data: {'review_note': ?reviewNote},
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

  Future<PurchaseOrderDetail> orderDetail(int purchaseOrderId) async {
    final resp = await api.dio.get<Map<String, dynamic>>(
      '/purchasing/orders/$purchaseOrderId/detail',
    );
    return PurchaseOrderDetail.fromJson(resp.data!);
  }

  Future<SupplierLedger> supplierLedger(int supplierId) async {
    final resp = await api.dio.get<Map<String, dynamic>>(
      '/purchasing/suppliers/$supplierId/ledger',
    );
    return SupplierLedger.fromJson(resp.data!);
  }

  // ---- Automation settings ----

  Future<PurchasingSettings> settings() async {
    final resp = await api.dio.get<Map<String, dynamic>>('/purchasing/settings');
    return PurchasingSettings.fromJson(resp.data!);
  }

  Future<PurchasingSettings> updateSettings(PurchasingSettings settings) async {
    final resp = await api.dio.put<Map<String, dynamic>>(
      '/purchasing/settings',
      data: settings.toJson(),
    );
    return PurchasingSettings.fromJson(resp.data!);
  }

  // ---- Purchase invoices ----

  Future<List<PurchaseInvoice>> invoices({String? status, PaginationParams pagination = PaginationParams.purchasing}) async {
    final resp = await api.dio.get<List<dynamic>>(
      '/purchasing/invoices',
      queryParameters: {'status': ?status, ...pagination.toQuery()},
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

  Future<List<SupplierPayment>> payments({String? status, PaginationParams pagination = PaginationParams.purchasing}) async {
    final resp = await api.dio.get<List<dynamic>>(
      '/purchasing/payments',
      queryParameters: {'status': ?status, ...pagination.toQuery()},
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
