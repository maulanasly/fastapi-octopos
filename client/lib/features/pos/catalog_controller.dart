/// Catalog cache for the POS grid. First load pulls the full catalog via
/// /sync/catalog (storing the server watermark); later refreshes request
/// only the delta since the watermark and merge it into the in-memory
/// cache. Falls back to a plain full pull when the delta path is
/// unavailable.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/auth_controller.dart';
import '../../core/db/database_provider.dart';
import '../../core/errors.dart';
import '../../core/local_persistence.dart';
import '../../core/models.dart';
import '../../core/strings.dart';

class CatalogState {
  final List<Category> categories;
  final List<Product> products;
  final bool loading;
  final String? error;

  const CatalogState({
    this.categories = const [],
    this.products = const [],
    this.loading = true,
    this.error,
  });
}

class CatalogController extends Notifier<CatalogState> {
  @override
  CatalogState build() {
    // Sign-out drops the in-memory cache and the stored watermark so the
    // next session starts from a clean full pull (no cross-user leakage).
    ref.listen<AuthState>(authControllerProvider, (prev, next) {
      if (prev?.status == AuthStatus.signedIn &&
          next.status == AuthStatus.signedOut) {
        ref.read(localStoreProvider).clearWatermark();
        // Drift: also clear DB watermark and catalog tables
        final db = ref.read(appDatabaseProvider);
        db.clearWatermark();
        // Don't await: fire and forget, but keep in-memory cleared
        state = const CatalogState();
      } else if (next.status == AuthStatus.signedIn &&
          prev?.status != AuthStatus.signedIn) {
        // Fresh session: repopulate (freshSession forces a full pull
        // because the cache was just reset).
        _load(freshSession: true);
      }
    });
    // Defer past the synchronous build phase: `_load` reads and writes
    // `state`, which is illegal while the notifier is still building.
    Future.microtask(() => _load(freshSession: true));
    return const CatalogState();
  }

  Future<void> _load({bool freshSession = false}) async {
    final db = ref.read(appDatabaseProvider);
    final store = ref.read(localStoreProvider);
    try {
      // Show cached DB data immediately for instant browse (even on freshSession
      // we can show stale cache while fetching full catalog in background).
      try {
        final cachedProducts = await db.getAllProducts();
        final cachedCategories = await db.getAllCategories();
        if (cachedProducts.isNotEmpty || cachedCategories.isNotEmpty) {
          state = CatalogState(
            categories: cachedCategories,
            products: cachedProducts,
            loading: false,
          );
        }
      } catch (_) {
        // DB read failure shouldn't block network fetch
      }

      // A stored watermark is only meaningful on top of a populated
      // cache: with an empty base (fresh sign-in) it must be ignored,
      // otherwise the delta pull returns just the changed rows and most
      // of the catalog would be missing from the POS grid.
      String? since;
      if (!freshSession) {
        since = await db.readWatermark() ?? await store.readWatermark();
      }
      final delta = await _fetchDelta(since);

      if (delta != null) {
        // Persist deletions first
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
        await store.writeWatermark(delta.serverTime);
        final merged = await _mergeWithDb(delta);
        state = CatalogState(
          categories: merged.categories,
          products: merged.products,
          loading: false,
        );
        return;
      }

      // Fallback: plain full pull (delta endpoint unavailable).
      // If we already have cached state, keep it unless full pull succeeds.
      final hasCached = state.products.isNotEmpty || state.categories.isNotEmpty;
      try {
        final repo = ref.read(catalogRepositoryProvider);
        final categories = await repo.categories();
        final products = await repo.products();
        // Persist full pull to DB for offline
        final now = DateTime.now().toIso8601String();
        if (products.isNotEmpty) await db.upsertProducts(products, now);
        if (categories.isNotEmpty) await db.upsertCategories(categories, now);
        await db.writeWatermark(now);
        await store.writeWatermark(now);
        state = CatalogState(
          categories: categories,
          products: products,
          loading: false,
        );
      } catch (e) {
        if (hasCached) {
          // Keep cached data, but surface offline error subtly
          state = CatalogState(
            categories: state.categories,
            products: state.products,
            loading: false,
            error: null,
          );
          return;
        }
        rethrow;
      }
    } catch (e) {
      // If DB has data, prefer showing it over error
      try {
        final cachedProducts = await db.getAllProducts();
        final cachedCategories = await db.getAllCategories();
        if (cachedProducts.isNotEmpty || cachedCategories.isNotEmpty) {
          state = CatalogState(
            categories: cachedCategories,
            products: cachedProducts,
            loading: false,
          );
          return;
        }
      } catch (_) {}
      state = CatalogState(
        loading: false,
        error: friendlyError(e, ref.read(stringsProvider)),
      );
    }
  }

  Future<CatalogDelta?> _fetchDelta(String? since) async {
    try {
      return await ref.read(syncRepositoryProvider).catalog(since: since);
    } catch (_) {
      return null;
    }
  }

  /// A delta carries only changed rows; merge it over the current cache
  /// plus apply deletions persisted in DB. Falls back to DB as source of truth.
  Future<CatalogDelta> _mergeWithDb(CatalogDelta delta) async {
    final db = ref.read(appDatabaseProvider);
    try {
      final allProducts = await db.getAllProducts();
      final allCategories = await db.getAllCategories();
      return CatalogDelta(
        serverTime: delta.serverTime,
        products: allProducts,
        categories: allCategories,
      );
    } catch (_) {
      // Fallback to in-memory merge if DB read fails
      return _mergeWithCurrent(delta);
    }
  }

  /// A delta carries only changed rows; merge it over the current cache.
  CatalogDelta _mergeWithCurrent(CatalogDelta delta) {
    if (state.products.isEmpty && state.categories.isEmpty) {
      return delta;
    }
    final productsById = <int, Product>{
      for (final p in state.products) p.id: p,
    };
    for (final p in delta.products) {
      productsById[p.id] = p;
    }
    // Apply deletions
    for (final id in delta.deletedProductIds) {
      productsById.remove(id);
    }
    final categoriesById = <int, Category>{
      for (final c in state.categories) c.id: c,
    };
    for (final c in delta.categories) {
      categoriesById[c.id] = c;
    }
    for (final id in delta.deletedCategoryIds) {
      categoriesById.remove(id);
    }
    return CatalogDelta(
      serverTime: delta.serverTime,
      products: productsById.values.toList(),
      categories: categoriesById.values.toList(),
      deletedProductIds: const [],
      deletedCategoryIds: const [],
    );
  }

  Future<void> refresh() async {
    // Keep the current cache as the merge base for the delta pull.
    await _load();
  }
}

final catalogControllerProvider =
    NotifierProvider<CatalogController, CatalogState>(CatalogController.new);
