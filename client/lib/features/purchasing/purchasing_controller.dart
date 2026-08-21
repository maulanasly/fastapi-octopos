/// Purchasing hub controller: suppliers, purchase orders, invoices and
/// supplier payments, with per-list status filters. Extracted from
/// purchasing_screen so the screen renders state instead of orchestrating
/// four parallel futures.
library;

import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/auth_controller.dart';
import '../../core/errors.dart';
import '../../core/models.dart';
import '../../core/strings.dart';

final purchasingControllerProvider =
    NotifierProvider<PurchasingController, PurchasingState>(
      PurchasingController.new,
    );

class PurchasingState {
  const PurchasingState({
    this.suppliers = const [],
    this.orders = const [],
    this.invoices = const [],
    this.payments = const [],
    this.orderStatus,
    this.invoiceStatus,
    this.paymentStatus,
    this.loading = true,
    this.error,
  });

  final List<Supplier> suppliers;
  final List<PurchaseOrder> orders;
  final List<PurchaseInvoice> invoices;
  final List<SupplierPayment> payments;

  /// Active list filters (null shows every status).
  final String? orderStatus;
  final String? invoiceStatus;
  final String? paymentStatus;

  final bool loading;
  final String? error;
}

class PurchasingController extends Notifier<PurchasingState> {
  @override
  PurchasingState build() {
    // Session-scoped: sign-out drops tenant data and filters.
    ref.listen<AuthState>(authControllerProvider, (prev, next) {
      if (prev?.status == AuthStatus.signedIn &&
          next.status == AuthStatus.signedOut) {
        state = const PurchasingState();
      } else if (next.status == AuthStatus.signedIn &&
          prev?.status != AuthStatus.signedIn) {
        reload();
      }
    });
    // Defer past the synchronous build phase.
    Future.microtask(reload);
    return const PurchasingState();
  }

  /// Re-fetches all four lists with the active status filters applied.
  Future<void> reload() async {
    final repo = ref.read(purchasingRepositoryProvider);
    try {
      final results = await <Future<Object?>>[
        repo.suppliers(),
        repo.orders(status: state.orderStatus),
        repo.invoices(status: state.invoiceStatus),
        repo.payments(status: state.paymentStatus),
      ].wait;
      if (!ref.mounted) return;
      state = PurchasingState(
        suppliers: results[0] as List<Supplier>,
        orders: results[1] as List<PurchaseOrder>,
        invoices: results[2] as List<PurchaseInvoice>,
        payments: results[3] as List<SupplierPayment>,
        orderStatus: state.orderStatus,
        invoiceStatus: state.invoiceStatus,
        paymentStatus: state.paymentStatus,
        loading: false,
      );
    } catch (e) {
      if (!ref.mounted) return;
      // Keep the last known lists; the views surface the failure with a
      // retry affordance.
      state = PurchasingState(
        suppliers: state.suppliers,
        orders: state.orders,
        invoices: state.invoices,
        payments: state.payments,
        orderStatus: state.orderStatus,
        invoiceStatus: state.invoiceStatus,
        paymentStatus: state.paymentStatus,
        loading: false,
        error: friendlyError(e, ref.read(stringsProvider)),
      );
    }
  }

  Future<void> setOrderStatus(String? status) {
    state = _copy(orderStatus: status);
    return reload();
  }

  Future<void> setInvoiceStatus(String? status) {
    state = _copy(invoiceStatus: status);
    return reload();
  }

  Future<void> setPaymentStatus(String? status) {
    state = _copy(paymentStatus: status);
    return reload();
  }

  /// copyWith variant where the three nullable filter fields use a
  /// sentinel so an explicit `null` resets the filter.
  static const _unset = Object();

  PurchasingState _copy({
    Object? orderStatus = _unset,
    Object? invoiceStatus = _unset,
    Object? paymentStatus = _unset,
  }) => PurchasingState(
    suppliers: state.suppliers,
    orders: state.orders,
    invoices: state.invoices,
    payments: state.payments,
    orderStatus: identical(orderStatus, _unset)
        ? state.orderStatus
        : orderStatus as String?,
    invoiceStatus: identical(invoiceStatus, _unset)
        ? state.invoiceStatus
        : invoiceStatus as String?,
    paymentStatus: identical(paymentStatus, _unset)
        ? state.paymentStatus
        : paymentStatus as String?,
    loading: state.loading,
    error: state.error,
  );
}
