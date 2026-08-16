/// Catalog cache for the POS grid, refreshed from the API.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/models.dart';

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

  Future<void> refresh() async {
    state = const CatalogState();
    await _load();
  }
}

final catalogControllerProvider =
    NotifierProvider<CatalogController, CatalogState>(CatalogController.new);
