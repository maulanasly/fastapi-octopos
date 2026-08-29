library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api_client.dart';
import '../models.dart';
import '../pagination.dart';

final reportRepositoryProvider = Provider<ReportRepository>(
  (ref) => ReportRepository(ref.watch(apiClientProvider)),
);

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

  Future<List<TopProductItem>> topProducts({String? startDate, String? endDate, PaginationParams pagination = const PaginationParams(limit: 10)}) async {
    final resp = await api.dio.get<List<dynamic>>(
      '/reports/top-products',
      queryParameters: {
        'start_date': ?startDate,
        'end_date': ?endDate,
        ...pagination.toQuery(),
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

  Future<SupplierSpendSummary> supplierSpend({
    String? startDate,
    String? endDate,
  }) async {
    final resp = await api.dio.get<Map<String, dynamic>>(
      '/reports/supplier-spend',
      queryParameters: {'start_date': ?startDate, 'end_date': ?endDate},
    );
    return SupplierSpendSummary.fromJson(resp.data!);
  }

  Future<VarianceTrendSummary> purchaseVariance({
    String? startDate,
    String? endDate,
  }) async {
    final resp = await api.dio.get<Map<String, dynamic>>(
      '/reports/purchase-variance',
      queryParameters: {'start_date': ?startDate, 'end_date': ?endDate},
    );
    return VarianceTrendSummary.fromJson(resp.data!);
  }
}
