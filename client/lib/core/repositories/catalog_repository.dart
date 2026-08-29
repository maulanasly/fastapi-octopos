library;

import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api_client.dart';
import '../models.dart';

final catalogRepositoryProvider = Provider<CatalogRepository>(
  (ref) => CatalogRepository(ref.watch(apiClientProvider)),
);

/// Curated category color palette from the backend (fallback list for
/// offline use keeps the same tones).
final categoryColorPaletteProvider = FutureProvider<List<String>>((ref) async {
  try {
    return await ref.watch(catalogRepositoryProvider).categoryColorPalette();
  } catch (_) {
    return const [
      '#E8F5E9',
      '#E3F2FD',
      '#FFF3E0',
      '#FCE4EC',
      '#F3E5F5',
      '#E0F2F1',
      '#FFFDE7',
      '#EFEBE9',
    ];
  }
});

class CatalogRepository {
  final ApiClient api;
  CatalogRepository(this.api);

  Future<List<Category>> categories() async {
    final resp = await api.dio.get<List<dynamic>>('/products/categories');
    return resp.data!
        .map((e) => Category.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<Product>> products() async {
    final resp = await api.dio.get<List<dynamic>>(
      '/products/',
      queryParameters: {'limit': 500},
    );
    return resp.data!
        .map((e) => Product.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Semantic catalog search over product embeddings (pgvector).
  Future<List<Product>> searchProducts(String query) async {
    final resp = await api.dio.get<List<dynamic>>(
      '/products/search',
      queryParameters: {'q': query},
    );
    return resp.data!
        .map((e) => Product.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Category> createCategory(
    String name,
    String? description, {
    String? color,
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/products/categories',
      data: {
        'name': name,
        'description': description,
        'color': ?color,
      },
    );
    return Category.fromJson(resp.data!);
  }

  /// Curated category color palette (single source of truth with the admin).
  Future<List<String>> categoryColorPalette() async {
    final resp = await api.dio.get<List<dynamic>>(
      '/products/categories/colors',
    );
    return resp.data!.cast<String>();
  }

  /// Sets (or clears, with null) a category's display color.
  Future<Category> updateCategoryColor(int categoryId, String? color) async {
    final resp = await api.dio.put<Map<String, dynamic>>(
      '/products/categories/$categoryId',
      data: {
        'color': ?color,
        if (color == null) 'color': null,
      },
    );
    return Category.fromJson(resp.data!);
  }

  Future<Product> createProduct(Map<String, dynamic> body) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/products/',
      data: body,
    );
    return Product.fromJson(resp.data!);
  }

  Future<Product> updateProduct(int id, Map<String, dynamic> body) async {
    final resp = await api.dio.put<Map<String, dynamic>>(
      '/products/$id/',
      data: body,
    );
    return Product.fromJson(resp.data!);
  }

  /// Uploads a product photo (multipart). Returns the updated product.
  Future<Product> uploadImage(
    int productId,
    Uint8List bytes,
    String filename,
  ) async {
    final form = FormData.fromMap({
      'file': MultipartFile.fromBytes(
        bytes,
        filename: filename,
        contentType: DioMediaType.parse(_mediaTypeFor(filename)),
      ),
    });
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/products/$productId/image',
      data: form,
    );
    return Product.fromJson(resp.data!);
  }

  /// Removes the product photo.
  Future<Product> deleteImage(int productId) async {
    final resp = await api.dio.delete<Map<String, dynamic>>(
      '/products/$productId/image',
    );
    return Product.fromJson(resp.data!);
  }

  static String _mediaTypeFor(String filename) {
    final lower = filename.toLowerCase();
    if (lower.endsWith('.png')) return 'image/png';
    if (lower.endsWith('.webp')) return 'image/webp';
    return 'image/jpeg';
  }
}
