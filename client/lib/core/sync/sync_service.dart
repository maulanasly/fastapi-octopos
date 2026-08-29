import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api_repositories.dart';
import '../db/app_database.dart';
import '../db/database_provider.dart';
import 'outbox_repository.dart';

final syncServiceProvider = Provider<SyncService>((ref) {
  final db = ref.watch(appDatabaseProvider);
  final orderRepo = ref.watch(orderRepositoryProvider);
  final syncRepo = ref.watch(syncRepositoryProvider);
  final outbox = ref.watch(outboxRepositoryProvider);
  return SyncService(
    db: db,
    orderRepo: orderRepo,
    syncRepo: syncRepo,
    outbox: outbox,
  );
});

class SyncService {
  final AppDatabase db;
  final OrderRepository orderRepo;
  final SyncRepository syncRepo;
  final OutboxRepository outbox;

  bool _running = false;

  SyncService({
    required this.db,
    required this.orderRepo,
    required this.syncRepo,
    required this.outbox,
  });

  /// Pull catalog delta and persist to drift + update watermark.
  /// Returns true on success.
  Future<bool> syncCatalog({bool fresh = false}) async {
    try {
      final since = fresh ? null : await db.readWatermark();
      final delta = await syncRepo.catalog(since: since);
      // Persist deletes first
      await db.deleteProductsById(delta.deletedProductIds);
      await db.deleteCategoriesById(delta.deletedCategoryIds);
      await db.upsertProducts(delta.products, delta.serverTime);
      await db.upsertCategories(delta.categories, delta.serverTime);
      await db.writeWatermark(delta.serverTime);
      return true;
    } on DioException {
      return false;
    } catch (_) {
      return false;
    }
  }

  /// Push pending outbox orders to backend. Idempotent via stored key.
  /// Each successful post marks row synced (then deleted) to keep table small.
  /// After order creation, payment is settled (single or split) if queued.
  Future<int> syncOutbox() async {
    if (_running) return 0;
    _running = true;
    int synced = 0;
    try {
      final pending = await outbox.pendingOrders();
      for (final row in pending) {
        try {
          final items = (jsonDecode(row.itemsJson) as List)
              .map((e) => e as Map<String, dynamic>)
              .toList();
          final order = await orderRepo.createOrder(
            items: items,
            customerId: row.customerId,
            promotionCode: row.promotionCode,
            redeemPoints: row.redeemPoints,
            destinationAddress: row.destinationAddress,
            destinationLat: row.destinationLat,
            destinationLng: row.destinationLng,
            idempotencyKey: row.idempotencyKey,
          );
          // Settle payment if queued
          if (row.splitJson != null && row.splitJson!.isNotEmpty) {
            final payments = (jsonDecode(row.splitJson!) as List)
                .map((e) => (e as Map).map((k, v) => MapEntry(k as String, v as String)))
                .toList();
            try {
              await orderRepo.addSplitPayments(orderId: order.id, payments: payments);
            } on DioException catch (e) {
              if (e.response?.statusCode == 409) {
                // already settled, ignore
              } else {
                rethrow;
              }
            }
          } else if (row.paymentMethod != null && row.paymentAmountCents != null) {
            try {
              await orderRepo.addPayment(
                orderId: order.id,
                method: row.paymentMethod!,
                amountCents: row.paymentAmountCents!,
                idempotencyKey: row.payIdempotencyKey,
              );
            } on DioException catch (e) {
              if (e.response?.statusCode == 409) {
                // idempotent duplicate
              } else {
                rethrow;
              }
            }
          }
          await outbox.remove(row.id);
          synced++;
        } on DioException catch (e) {
          final code = e.response?.statusCode;
          // 409 = duplicate idempotent, also considered synced; 4xx other = failed (don't retry blindly)
          if (code == 409) {
            await outbox.remove(row.id);
            synced++;
          } else if (code != null && code >= 400 && code < 500) {
            await outbox.markFailed(row.id, e.message ?? 'client error $code');
          } else {
            // network/server error -> keep pending for next run
            await db.markOrderStatus(row.id, 'pending', error: e.message);
          }
        } catch (e) {
          await outbox.markFailed(row.id, e.toString());
        }
      }
    } finally {
      _running = false;
    }
    return synced;
  }

  /// Combined foreground sync: push then pull.
  Future<void> syncAll() async {
    await syncOutbox();
    await syncCatalog();
  }
}
