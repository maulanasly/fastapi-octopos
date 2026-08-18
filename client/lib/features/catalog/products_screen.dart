/// Manager screen: product & category CRUD with images and colors.
library;

import 'dart:async';
import 'dart:typed_data';

import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import '../../core/api_repositories.dart';
import '../../core/errors.dart';
import '../../core/colors.dart';
import '../../core/config.dart';
import '../../core/money.dart';
import '../../core/models.dart';
import '../../core/strings.dart';
import '../pos/catalog_controller.dart';

class ProductsScreen extends ConsumerStatefulWidget {
  const ProductsScreen({super.key});

  @override
  ConsumerState<ProductsScreen> createState() => _ProductsScreenState();
}

class _ProductsScreenState extends ConsumerState<ProductsScreen> {
  final _query = TextEditingController();
  Timer? _debounce;
  List<Product>? _results;
  String? _searchError;

  @override
  void dispose() {
    _debounce?.cancel();
    _query.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    final catalog = ref.watch(catalogControllerProvider);
    return Scaffold(
      appBar: AppBar(
        title: Text(s.of('products')),
        actions: [
          IconButton(
            tooltip: s.of('categories'),
            icon: const Icon(Icons.palette_outlined),
            onPressed: () => _manageCategories(context),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _createProduct(context),
        child: const Icon(Icons.add),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
            child: TextField(
              controller: _query,
              decoration: InputDecoration(
                hintText: s.of('searchProducts'),
                prefixIcon: const Icon(Icons.search),
                border: const OutlineInputBorder(),
                isDense: true,
                suffixIcon: _query.text.isEmpty
                    ? null
                    : IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          _query.clear();
                          setState(() {
                            _results = null;
                            _searchError = null;
                          });
                        },
                      ),
              ),
              onChanged: _onQueryChanged,
            ),
          ),
          Expanded(child: _buildList(context, catalog, s)),
        ],
      ),
    );
  }

  void _onQueryChanged(String q) {
    _debounce?.cancel();
    final query = q.trim();
    if (query.isEmpty) {
      setState(() {
        _results = null;
        _searchError = null;
      });
      return;
    }
    _debounce = Timer(const Duration(milliseconds: 400), () async {
      try {
        final results =
            await ref.read(catalogRepositoryProvider).searchProducts(query);
        if (!mounted) return;
        setState(() {
          _results = results;
          _searchError = null;
        });
      } catch (e) {
        if (!mounted) return;
        setState(() => _searchError = friendlyError(e, ref.read(stringsProvider)));
      }
    });
  }

  Widget _buildList(BuildContext context, CatalogState catalog, AppStrings s) {
    if (_results != null) {
      if (_results!.isEmpty) {
        return Center(
          child: Text(s.of('noSearchResults', args: {'q': _query.text.trim()})),
        );
      }
      return ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: _results!.length,
        separatorBuilder: (_, _) => const Divider(height: 8),
        itemBuilder: (context, i) {
          final product = _results![i];
          return _ProductTile(
            product: product,
            onTap: () => _editProduct(context, product),
          );
        },
      );
    }
    if (_searchError != null) {
      return Center(child: Text(_searchError!));
    }
    if (catalog.loading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (catalog.error != null) {
      return Center(child: Text('Failed to load:\n${catalog.error}'));
    }
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: catalog.products.length,
      separatorBuilder: (_, _) => const Divider(height: 8),
      itemBuilder: (context, i) {
        final product = catalog.products[i];
        return _ProductTile(
          product: product,
          onTap: () => _editProduct(context, product),
        );
      },
    );
  }

  Future<void> _createProduct(BuildContext context) async {
    await _productDialog(context);
  }

  Future<void> _editProduct(BuildContext context, Product product) async {
    await _productDialog(context, product: product);
  }

  Future<void> _manageCategories(BuildContext context) async {
    await showDialog<void>(
      context: context,
      builder: (_) => const CategoriesDialog(),
    );
  }

  Future<void> _productDialog(BuildContext context, {Product? product}) async {
    final s = ref.watch(stringsProvider);
    final categories = ref.read(catalogControllerProvider).categories;
    final name = TextEditingController(text: product?.name ?? '');
    final sku = TextEditingController(text: product?.sku ?? '');
    final price = TextEditingController(
      text: product == null ? '' : centsToApi(product.priceCents),
    );
    final stock = TextEditingController(
      text: (product?.stockQuantity ?? 0).toString(),
    );
    int? categoryId = product?.categoryId;
    Product? current = product;

    final saved = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (dialogContext, setDialogState) => AlertDialog(
          title: Text(
            product == null
                ? s.of('newProduct')
                : s.of('editProduct', args: {'name': product.name}),
          ),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (current != null)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: Column(
                      children: [
                        _ProductThumb(product: current!, size: 96),
                        const SizedBox(height: 8),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            TextButton.icon(
                              icon: const Icon(Icons.upload, size: 16),
                              label: Text(s.of('uploadPhoto')),
                              onPressed: () async {
                                final picked = await ImagePicker().pickImage(
                                  source: ImageSource.gallery,
                                );
                                if (picked == null) return;
                                final bytes = await picked.readAsBytes();
                                final updated = await ref
                                    .read(catalogRepositoryProvider)
                                    .uploadImage(
                                      current!.id,
                                      Uint8List.fromList(bytes),
                                      picked.name,
                                    );
                                setDialogState(() => current = updated);
                              },
                            ),
                            if (current!.imageUrl != null)
                              TextButton.icon(
                                icon: const Icon(
                                  Icons.delete_outline,
                                  size: 16,
                                ),
                                label: Text(s.of('removePhoto')),
                                onPressed: () async {
                                  final updated = await ref
                                      .read(catalogRepositoryProvider)
                                      .deleteImage(current!.id);
                                  setDialogState(() => current = updated);
                                },
                              ),
                          ],
                        ),
                      ],
                    ),
                  ),
                TextField(
                  controller: name,
                  decoration: InputDecoration(labelText: s.of('name')),
                ),
                TextField(
                  controller: sku,
                  decoration: InputDecoration(labelText: s.of('sku')),
                ),
                TextField(
                  controller: price,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(labelText: s.of('price')),
                ),
                TextField(
                  controller: stock,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(labelText: s.of('stock')),
                ),
                DropdownButtonFormField<int>(
                  initialValue: categoryId,
                  decoration: InputDecoration(labelText: s.of('category')),
                  items: [
                    for (final c in categories)
                      DropdownMenuItem(value: c.id, child: Text(c.name)),
                  ],
                  onChanged: (v) => categoryId = v,
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(false),
              child: Text(s.of('cancel')),
            ),
            FilledButton(
              onPressed: () => Navigator.of(dialogContext).pop(true),
              child: Text(s.of('save')),
            ),
          ],
        ),
      ),
    );

    if (saved != true) return;
    final body = {
      'name': name.text.trim(),
      'sku': sku.text.trim(),
      'price': double.tryParse(price.text) ?? 0,
      'stock_quantity': int.tryParse(stock.text) ?? 0,
      'category_id': ?categoryId,
    };
    try {
      if (product == null) {
        await ref.read(catalogRepositoryProvider).createProduct(body);
      } else {
        await ref
            .read(catalogRepositoryProvider)
            .updateProduct(product.id, body);
      }
      await ref.read(catalogControllerProvider.notifier).refresh();
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(friendlyError(e, ref.read(stringsProvider)))),
        );
      }
    }
  }
}

/// Category-colored monogram / thumbnail widget.
class _ProductThumb extends StatelessWidget {
  const _ProductThumb({required this.product, this.size = 40});

  final Product product;
  final double size;

  @override
  Widget build(BuildContext context) {
    final url = product.thumbnailUrl ?? product.imageUrl;
    if (url != null) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(8),
        child: CachedNetworkImage(
          imageUrl: '${AppConfig.mediaBaseUrl}$url',
          width: size,
          height: size,
          fit: BoxFit.cover,
          errorWidget: (_, _, _) => _monogram(context),
          placeholder: (_, _) => _monogram(context),
        ),
      );
    }
    return _monogram(context);
  }

  Widget _monogram(BuildContext context) {
    final color =
        colorFromHex(product.category?.color) ??
        Theme.of(context).colorScheme.surfaceContainerHighest;
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(8),
      ),
      alignment: Alignment.center,
      child: Text(
        product.name.isEmpty ? '?' : product.name[0].toUpperCase(),
        style: TextStyle(
          color: textColorOn(color),
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}

/// Category management dialog: create categories and set their colors.
class CategoriesDialog extends ConsumerStatefulWidget {
  const CategoriesDialog({super.key});

  @override
  ConsumerState<CategoriesDialog> createState() => _CategoriesDialogState();
}

class _CategoriesDialogState extends ConsumerState<CategoriesDialog> {
  final _name = TextEditingController();
  String? _color;

  @override
  void dispose() {
    _name.dispose();
    super.dispose();
  }

  Future<void> _create() async {
    final name = _name.text.trim();
    if (name.isEmpty) return;
    try {
      await ref
          .read(catalogRepositoryProvider)
          .createCategory(name, null, color: _color);
      _name.clear();
      setState(() => _color = null);
      await ref.read(catalogControllerProvider.notifier).refresh();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(friendlyError(e, ref.read(stringsProvider)))),
        );
      }
    }
  }

  Future<void> _editColor(Category category) async {
    final chosen = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(ref.read(stringsProvider).of('chooseColor')),
        content: Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (final hex
                in ref.watch(categoryColorPaletteProvider).value ??
                    const <String>[])
              InkWell(
                onTap: () => Navigator.of(ctx).pop(hex),
                child: Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: colorFromHex(hex),
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.black12),
                  ),
                  child: category.color == hex
                      ? const Icon(Icons.check, size: 18)
                      : null,
                ),
              ),
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(''),
              child: Text(ref.read(stringsProvider).of('noColor')),
            ),
          ],
        ),
      ),
    );
    if (chosen == null || !mounted) return;
    await ref
        .read(catalogRepositoryProvider)
        .updateCategoryColor(category.id, chosen.isEmpty ? null : chosen);
    await ref.read(catalogControllerProvider.notifier).refresh();
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    final catalog = ref.watch(catalogControllerProvider);
    return AlertDialog(
      title: Text(s.of('categories')),
      content: SizedBox(
        width: 380,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: _name,
              decoration: InputDecoration(
                labelText: s.of('name'),
                isDense: true,
              ),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: [
                for (final hex
                    in ref.watch(categoryColorPaletteProvider).value ??
                        const <String>[])
                  InkWell(
                    onTap: () => setState(() => _color = hex),
                    child: Container(
                      width: 28,
                      height: 28,
                      decoration: BoxDecoration(
                        color: colorFromHex(hex),
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: _color == hex
                              ? Theme.of(context).colorScheme.primary
                              : Colors.black12,
                          width: _color == hex ? 2 : 1,
                        ),
                      ),
                      child: _color == hex
                          ? const Icon(Icons.check, size: 14)
                          : null,
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 8),
            Align(
              alignment: Alignment.centerRight,
              child: FilledButton(
                onPressed: _create,
                child: Text(s.of('create')),
              ),
            ),
            const Divider(height: 24),
            Flexible(
              child: ListView(
                shrinkWrap: true,
                children: [
                  for (final category in catalog.categories)
                    ListTile(
                      dense: true,
                      leading: Container(
                        width: 20,
                        height: 20,
                        decoration: BoxDecoration(
                          color: colorFromHex(category.color),
                          shape: BoxShape.circle,
                          border: Border.all(color: Colors.black12),
                        ),
                      ),
                      title: Text(category.name),
                      trailing: const Icon(Icons.edit, size: 16),
                      onTap: () => _editColor(category),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: Text(s.of('done')),
        ),
      ],
    );
  }
}

class _ProductTile extends StatelessWidget {
  const _ProductTile({required this.product, required this.onTap});

  final Product product;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final color = product.category?.color;
    return ListTile(
      leading: _ProductThumb(product: product),
      title: Text(product.name),
      subtitle: Text(
        '${product.sku} · ${formatCents(product.priceCents)} · '
        '${product.stockQuantity} in stock',
      ),
      trailing: color == null
          ? null
          : Container(
              width: 14,
              height: 14,
              decoration: BoxDecoration(
                color: colorFromHex(color),
                shape: BoxShape.circle,
              ),
            ),
      onTap: onTap,
    );
  }
}
