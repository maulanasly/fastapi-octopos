import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import '../db/app_database.dart';
import '../db/database_provider.dart';

const _uuid = Uuid();

final outboxRepositoryProvider = Provider<OutboxRepository>((ref) {
  final db = ref.watch(appDatabaseProvider);
  return OutboxRepository(db);
});

class OutboxRepository {
  final AppDatabase db;
  OutboxRepository(this.db);

  Future<int> enqueueOrder({
    int? customerId,
    required List<Map<String, dynamic>> items,
    String? promotionCode,
    int redeemPoints = 0,
    String? destinationAddress,
    double? destinationLat,
    double? destinationLng,
    String? idempotencyKey,
    String? paymentMethod,
    int? paymentAmountCents,
    String? splitJson,
    String? payIdempotencyKey,
  }) {
    final key = idempotencyKey ?? _uuid.v4();
    return db.enqueueOrder(
      customerId: customerId,
      itemsJson: jsonEncode(items),
      promotionCode: promotionCode,
      redeemPoints: redeemPoints,
      destinationAddress: destinationAddress,
      destinationLat: destinationLat,
      destinationLng: destinationLng,
      idempotencyKey: key,
      paymentMethod: paymentMethod,
      paymentAmountCents: paymentAmountCents,
      splitJson: splitJson,
      payIdempotencyKey: payIdempotencyKey,
    );
  }

  Future<List<OutboxOrder>> pendingOrders() => db.pendingOrders();

  Future<void> markSynced(int id) => db.markOrderStatus(id, 'synced');

  Future<void> markFailed(int id, String error) => db.markOrderStatus(id, 'failed', error: error);

  Future<void> remove(int id) => db.deleteOrder(id);

  Future<void> clearAll() => db.clearAllOutbox();

  Stream<List<OutboxOrder>> watchPending() {
    return (db.select(db.outboxOrders)..where((t) => t.status.equals('pending'))).watch();
  }
}
