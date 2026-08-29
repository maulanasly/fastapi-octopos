import 'package:dio/dio.dart';
import 'package:workmanager/workmanager.dart';

import '../config.dart';
import '../db/app_database.dart';
import '../models/catalog.dart';

const syncTask = 'com.octopos.sync';
const outboxTask = 'com.octopos.outbox';

@pragma('vm:entry-point')
void callbackDispatcher() {
  Workmanager().executeTask((task, inputData) async {
    final db = AppDatabase();
    try {
      // Background catalog sync is best-effort; auth is required for
      // /sync/catalog so we skip if no token can be read in this isolate.
      // Foreground auto_sync will handle authenticated sync when online.
      if (task == syncTask || task == outboxTask) {
        final dio = Dio(
          BaseOptions(
            baseUrl: AppConfig.apiBaseUrl,
            connectTimeout: const Duration(seconds: 10),
            receiveTimeout: const Duration(seconds: 30),
            headers: {'Accept': 'application/json'},
          ),
        );
        try {
          final resp = await dio.get<Map<String, dynamic>>('/sync/catalog');
          final delta = CatalogDelta.fromJson(resp.data!);
          // Persist
          if (delta.deletedProductIds.isNotEmpty) {
            await db.deleteProductsById(delta.deletedProductIds);
          }
          if (delta.deletedCategoryIds.isNotEmpty) {
            await db.deleteCategoriesById(delta.deletedCategoryIds);
          }
          if (delta.products.isNotEmpty) {
            await db.upsertProducts(delta.products, delta.serverTime);
          }
          if (delta.categories.isNotEmpty) {
            await db.upsertCategories(delta.categories, delta.serverTime);
          }
          await db.writeWatermark(delta.serverTime);
        } catch (_) {
          // ignore sync failure (likely 401 offline auth)
        } finally {
          dio.close();
        }
      }
    } catch (_) {
    } finally {
      await db.close();
    }
    return Future.value(true);
  });
}
