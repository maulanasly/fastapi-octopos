/// Catalog cache for the POS grid. First load pulls the full catalog via
/// /sync/catalog (storing the server watermark); later refreshes request
/// only the delta since the watermark and merge it into the in-memory
/// cache. Falls back to a plain full pull when the delta path is
/// unavailable.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/models.dart';
import 'cart_controller.dart' show localStoreProvider;

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
    _load();
    return const CatalogState();
  }

  Future<void> _load() async {
    try {
      final store = ref.read(localStoreProvider);
      final since = await store.readWatermark();
      final delta = await _fetchDelta(since);

      if (delta != null) {
        await store.writeWatermark(delta.serverTime);
        final merged = _mergeWithCurrent(delta);
        state = CatalogState(
          categories: merged.categories,
          products: merged.products,
          loading: false,
        );
        return;
      }

      // Fallback: plain full pull (delta endpoint unavailable).
      final repo = ref.read(catalogRepositoryProvider);
      final categories = await repo.categories();
      final products = await repo.products();
      state = CatalogState(
        categories: categories,
        products: products,
        loading: false,
      );
    } catch (e) {
      state = CatalogState(loading: false, error: e.toString());
    }
  }

  Future<CatalogDelta?> _fetchDelta(String? since) async {
    try {
      return await ref.read(syncRepositoryProvider).catalog(since: since);
    } catch (_) {
      return null;
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
    final categoriesById = <int, Category>{
      for (final c in state.categories) c.id: c,
    };
    for (final c in delta.categories) {
      categoriesById[c.id] = c;
    }
    return CatalogDelta(
      serverTime: delta.serverTime,
      products: productsById.values.toList(),
      categories: categoriesById.values.toList(),
    );
  }

  Future<void> refresh() async {
    // Keep the current cache as the merge base for the delta pull.
    await _load();
  }
}

final catalogControllerProvider =
    NotifierProvider<CatalogController, CatalogState>(CatalogController.new);
