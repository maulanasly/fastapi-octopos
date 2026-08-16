/// Manager screen: product & category CRUD.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/strings.dart';
import '../../core/money.dart';
import '../../core/models.dart';
import '../pos/catalog_controller.dart';

class ProductsScreen extends ConsumerStatefulWidget {
  const ProductsScreen({super.key});

  @override
  ConsumerState<ProductsScreen> createState() => _ProductsScreenState();
}

class _ProductsScreenState extends ConsumerState<ProductsScreen> {
  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    final catalog = ref.watch(catalogControllerProvider);
    return Scaffold(
      appBar: AppBar(title: Text(s.of('products'))),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _createProduct(context),
        child: const Icon(Icons.add),
      ),
      body: catalog.loading
          ? const Center(child: CircularProgressIndicator())
          : catalog.error != null
          ? Center(child: Text('Failed to load:\n${catalog.error}'))
          : ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: catalog.products.length,
              separatorBuilder: (_, _) => const Divider(height: 8),
              itemBuilder: (context, i) {
                final product = catalog.products[i];
                return ListTile(
                  leading: CircleAvatar(
                    child: Text(product.name.characters.first),
                  ),
                  title: Text(product.name),
                  subtitle: Text(
                    '${product.sku} · ${formatCents(product.priceCents)} · '
                    '${product.stockQuantity} in stock',
                  ),
                  trailing: Text(product.category?.name ?? ''),
                  onTap: () => _editProduct(context, product),
                );
              },
            ),
    );
  }

  Future<void> _createProduct(BuildContext context) async {
    await _productDialog(context);
  }

  Future<void> _editProduct(BuildContext context, Product product) async {
    await _productDialog(context, product: product);
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

    final saved = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(
          product == null
              ? s.of('newProduct')
              : s.of('editProduct', args: {'name': product.name}),
        ),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
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
                value: categoryId,
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
    );

    if (saved != true) return;
    final body = {
      'name': name.text.trim(),
      'sku': sku.text.trim(),
      'price': double.tryParse(price.text) ?? 0,
      'stock_quantity': int.tryParse(stock.text) ?? 0,
      if (categoryId != null) 'category_id': categoryId,
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
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Save failed: $e')));
      }
    }
  }
}
