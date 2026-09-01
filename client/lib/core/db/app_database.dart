import 'dart:convert';

import 'package:drift/drift.dart';
import 'package:drift_flutter/drift_flutter.dart';

import '../models/catalog.dart';

part 'app_database.g.dart';

class DriftProducts extends Table {
  IntColumn get id => integer()();
  TextColumn get name => text()();
  TextColumn get sku => text()();
  TextColumn get dataJson => text()();
  TextColumn get updatedAt => text()();
  @override
  Set<Column> get primaryKey => {id};
}

class DriftCategories extends Table {
  IntColumn get id => integer()();
  TextColumn get name => text()();
  TextColumn get dataJson => text()();
  TextColumn get updatedAt => text()();
  @override
  Set<Column> get primaryKey => {id};
}

class SyncMeta extends Table {
  TextColumn get key => text()();
  TextColumn get value => text().nullable()();
  @override
  Set<Column> get primaryKey => {key};
}

class OutboxOrders extends Table {
  IntColumn get id => integer().autoIncrement()();
  IntColumn get customerId => integer().nullable()();
  TextColumn get itemsJson => text()();
  TextColumn get promotionCode => text().nullable()();
  IntColumn get redeemPoints => integer().withDefault(const Constant(0))();
  TextColumn get destinationAddress => text().nullable()();
  RealColumn get destinationLat => real().nullable()();
  RealColumn get destinationLng => real().nullable()();
  TextColumn get idempotencyKey => text().customConstraint('UNIQUE NOT NULL')();
  TextColumn get status => text().withDefault(const Constant('pending'))();
  TextColumn get createdAt => text()();
  TextColumn get lastError => text().nullable()();
  TextColumn get paymentMethod => text().nullable()();
  IntColumn get paymentAmountCents => integer().nullable()();
  TextColumn get splitJson => text().nullable()();
  TextColumn get payIdempotencyKey => text().nullable()();
}

class OutboxPayments extends Table {
  IntColumn get id => integer().autoIncrement()();
  IntColumn get orderId => integer()();
  TextColumn get method => text()();
  IntColumn get amountCents => integer()();
  TextColumn get idempotencyKey => text().customConstraint('UNIQUE NOT NULL')();
  TextColumn get status => text().withDefault(const Constant('pending'))();
  TextColumn get createdAt => text()();
  TextColumn get lastError => text().nullable()();
}

@DriftDatabase(tables: [DriftProducts, DriftCategories, SyncMeta, OutboxOrders, OutboxPayments])
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(driftDatabase(name: 'octopos'));

  // For tests: in-memory
  AppDatabase.forTesting(super.e);

  @override
  int get schemaVersion => 2;

  @override
  MigrationStrategy get migration => MigrationStrategy(
    onCreate: (m) async => m.createAll(),
    onUpgrade: (m, from, to) async {
      if (from < 2) {
        await m.addColumn(outboxOrders, outboxOrders.paymentMethod);
        await m.addColumn(outboxOrders, outboxOrders.paymentAmountCents);
        await m.addColumn(outboxOrders, outboxOrders.splitJson);
        await m.addColumn(outboxOrders, outboxOrders.payIdempotencyKey);
      }
    },
  );

  // ---- Catalog ----

  Future<void> upsertProducts(List<Product> products, String serverTime) async {
    await batch((b) {
      for (final p in products) {
        b.insert(
          driftProducts,
          DriftProductsCompanion.insert(
            id: Value(p.id),
            name: p.name,
            sku: p.sku,
            dataJson: jsonEncode(p.toJson()),
            updatedAt: serverTime,
          ),
          mode: InsertMode.insertOrReplace,
        );
      }
    });
  }

  Future<void> upsertCategories(List<Category> categories, String serverTime) async {
    await batch((b) {
      for (final c in categories) {
        b.insert(
          driftCategories,
          DriftCategoriesCompanion.insert(
            id: Value(c.id),
            name: c.name,
            dataJson: jsonEncode(c.toJson()),
            updatedAt: serverTime,
          ),
          mode: InsertMode.insertOrReplace,
        );
      }
    });
  }

  Future<void> deleteProductsById(List<int> ids) async {
    if (ids.isEmpty) return;
    await (delete(driftProducts)..where((t) => t.id.isIn(ids))).go();
  }

  Future<void> deleteCategoriesById(List<int> ids) async {
    if (ids.isEmpty) return;
    await (delete(driftCategories)..where((t) => t.id.isIn(ids))).go();
  }

  Future<List<Product>> getAllProducts() async {
    final rows = await select(driftProducts).get();
    return rows.map((r) => Product.fromJson(jsonDecode(r.dataJson) as Map<String, dynamic>)).toList();
  }

  Future<List<Category>> getAllCategories() async {
    final rows = await select(driftCategories).get();
    return rows.map((r) => Category.fromJson(jsonDecode(r.dataJson) as Map<String, dynamic>)).toList();
  }

  // ---- SyncMeta ----

  Future<String?> readWatermark() async {
    final row = await (select(syncMeta)..where((t) => t.key.equals('catalog_watermark'))).getSingleOrNull();
    return row?.value;
  }

  Future<void> writeWatermark(String iso) async {
    await into(syncMeta).insertOnConflictUpdate(
      SyncMetaCompanion.insert(key: 'catalog_watermark', value: Value(iso)),
    );
  }

  Future<void> clearWatermark() async {
    await (delete(syncMeta)..where((t) => t.key.equals('catalog_watermark'))).go();
  }

  Future<void> clearCatalog() async {
    await delete(driftProducts).go();
    await delete(driftCategories).go();
  }

  // ---- OutboxOrders ----

  Future<int> enqueueOrder({
    int? customerId,
    required String itemsJson,
    String? promotionCode,
    int redeemPoints = 0,
    String? destinationAddress,
    double? destinationLat,
    double? destinationLng,
    required String idempotencyKey,
    String? paymentMethod,
    int? paymentAmountCents,
    String? splitJson,
    String? payIdempotencyKey,
  }) {
    return into(outboxOrders).insert(
      OutboxOrdersCompanion.insert(
        customerId: Value(customerId),
        itemsJson: itemsJson,
        promotionCode: Value(promotionCode),
        redeemPoints: Value(redeemPoints),
        destinationAddress: Value(destinationAddress),
        destinationLat: Value(destinationLat),
        destinationLng: Value(destinationLng),
        idempotencyKey: idempotencyKey,
        createdAt: DateTime.now().toIso8601String(),
        paymentMethod: Value(paymentMethod),
        paymentAmountCents: Value(paymentAmountCents),
        splitJson: Value(splitJson),
        payIdempotencyKey: Value(payIdempotencyKey),
      ),
    );
  }

  Future<List<OutboxOrder>> pendingOrders() =>
      (select(outboxOrders)..where((t) => t.status.equals('pending'))).get();

  Future<void> markOrderStatus(int id, String status, {String? error}) async {
    await (update(outboxOrders)..where((t) => t.id.equals(id))).write(
      OutboxOrdersCompanion(
        status: Value(status),
        lastError: Value(error),
      ),
    );
  }

  Future<void> deleteOrder(int id) async {
    await (delete(outboxOrders)..where((t) => t.id.equals(id))).go();
  }

  Future<void> clearAllOutbox() async {
    await delete(outboxOrders).go();
    await delete(outboxPayments).go();
  }
}
