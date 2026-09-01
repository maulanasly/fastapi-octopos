library;

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api_client.dart';
import '../models.dart';

final drawerRepositoryProvider = Provider<DrawerRepository>(
  (ref) => DrawerRepository(ref.watch(apiClientProvider)),
);

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
