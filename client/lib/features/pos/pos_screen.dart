/// Cashier POS screen: catalog grid + cart + checkout + receipt.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api_repositories.dart';
import '../../core/money.dart';
import '../../core/models.dart';
import '../drawer/drawer_controller.dart';
import 'cart_controller.dart';
import 'catalog_controller.dart';
import 'checkout_sheet.dart';
import 'receipt_screen.dart';

class PosScreen extends ConsumerStatefulWidget {
  const PosScreen({super.key});

  @override
  ConsumerState<PosScreen> createState() => _PosScreenState();
}

class _PosScreenState extends ConsumerState<PosScreen> {
  int? _selectedCategoryId;
  String _search = '';

  @override
  Widget build(BuildContext context) {
    final catalog = ref.watch(catalogControllerProvider);
    final cart = ref.watch(cartControllerProvider);
    final drawer = ref.watch(drawerControllerProvider);

    final products = _filtered(catalog.products);

    return Column(
      children: [
        if (drawer.session == null && !drawer.loading)
          MaterialBanner(
            content: const Text(
              'No open drawer. Open one before taking orders.',
            ),
            leading: const Icon(Icons.info_outline),
            actions: [
              TextButton(
                onPressed: () => _openDrawer(context),
                child: const Text('Open drawer'),
              ),
            ],
          )
        else if (drawer.session != null)
          MaterialBanner(
            content: Text('Drawer #${drawer.session!.id} open'),
            leading: const Icon(Icons.lock_open),
            actions: [
              TextButton(
                onPressed: () => context.push('/reconcile'),
                child: const Text('End shift'),
              ),
            ],
          ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8),
          child: Row(
            children: [
              TextButton.icon(
                icon: const Icon(Icons.assignment_return, size: 18),
                label: const Text('Refunds'),
                onPressed: () => context.push('/refunds'),
              ),
              const Spacer(),
              IconButton(
                tooltip: 'Refresh catalog',
                icon: const Icon(Icons.refresh),
                onPressed: () =>
                    ref.read(catalogControllerProvider.notifier).refresh(),
              ),
            ],
          ),
        ),
        Expanded(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Expanded(
                flex: 3,
                child: _catalogPane(context, catalog, products),
              ),
              VerticalDivider(width: 1),
              Expanded(flex: 2, child: _cartPane(context, cart)),
            ],
          ),
        ),
      ],
    );
  }

  List<Product> _filtered(List<Product> products) {
    var list = products;
    if (_selectedCategoryId != null) {
      list = list.where((p) => p.categoryId == _selectedCategoryId).toList();
    }
    final q = _search.trim().toLowerCase();
    if (q.isNotEmpty) {
      list = list
          .where(
            (p) =>
                p.name.toLowerCase().contains(q) ||
                p.sku.toLowerCase().contains(q),
          )
          .toList();
    }
    return list;
  }

  Widget _catalogPane(
    BuildContext context,
    CatalogState catalog,
    List<Product> products,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.all(8),
          child: TextField(
            decoration: const InputDecoration(
              hintText: 'Search products…',
              prefixIcon: Icon(Icons.search),
              border: OutlineInputBorder(),
              isDense: true,
            ),
            onChanged: (v) => setState(() => _search = v),
          ),
        ),
        SizedBox(
          height: 40,
          child: ListView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 8),
            children: [
              Padding(
                padding: const EdgeInsets.only(right: 8),
                child: ChoiceChip(
                  label: const Text('All'),
                  selected: _selectedCategoryId == null,
                  onSelected: (_) => setState(() => _selectedCategoryId = null),
                ),
              ),
              for (final category in catalog.categories)
                Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: ChoiceChip(
                    label: Text(category.name),
                    selected: _selectedCategoryId == category.id,
                    onSelected: (_) =>
                        setState(() => _selectedCategoryId = category.id),
                  ),
                ),
            ],
          ),
        ),
        Expanded(
          child: catalog.loading
              ? const Center(child: CircularProgressIndicator())
              : catalog.error != null
              ? Center(child: Text('Failed to load catalog:\n${catalog.error}'))
              : GridView.builder(
                  padding: const EdgeInsets.all(8),
                  gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
                    maxCrossAxisExtent: 200,
                    childAspectRatio: 1.15,
                    mainAxisSpacing: 8,
                    crossAxisSpacing: 8,
                  ),
                  itemCount: products.length,
                  itemBuilder: (context, i) =>
                      _productTile(context, products[i]),
                ),
        ),
      ],
    );
  }

  Widget _productTile(BuildContext context, Product product) {
    final outOfStock = product.stockQuantity <= 0;
    return Card(
      color: outOfStock
          ? Theme.of(context).colorScheme.surfaceContainerHighest
          : null,
      child: InkWell(
        onTap: outOfStock
            ? null
            : () =>
                  ref.read(cartControllerProvider.notifier).addProduct(product),
        child: Padding(
          padding: const EdgeInsets.all(8),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                product.name,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.titleSmall,
              ),
              const Spacer(),
              Text(
                formatCents(product.priceCents),
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: Theme.of(context).colorScheme.primary,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                '${product.stockQuantity} in stock',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: outOfStock
                      ? Theme.of(context).colorScheme.error
                      : Colors.grey,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _cartPane(BuildContext context, CartState cart) {
    final canCheckout =
        cart.isEmpty || ref.read(drawerControllerProvider).session == null;
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              Text(
                'Cart (${cart.itemCount})',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const Spacer(),
              if (cart.customer != null)
                Chip(
                  label: Text(
                    cart.customer!.name,
                    overflow: TextOverflow.ellipsis,
                  ),
                  onDeleted: () => ref
                      .read(cartControllerProvider.notifier)
                      .setCustomer(null),
                )
              else
                OutlinedButton.icon(
                  icon: const Icon(Icons.person_add_alt, size: 16),
                  label: const Text('Customer'),
                  onPressed: () => _pickCustomer(context),
                ),
            ],
          ),
        ),
        Expanded(
          child: cart.isEmpty
              ? const Center(child: Text('Cart is empty'))
              : ListView.separated(
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  itemCount: cart.lines.length,
                  separatorBuilder: (_, _) => const Divider(height: 8),
                  itemBuilder: (context, i) {
                    final line = cart.lines.values.elementAt(i);
                    return ListTile(
                      dense: true,
                      title: Text(line.product.name),
                      subtitle: Text(
                        '${formatCents(line.product.priceCents)} × ${line.quantity}',
                      ),
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          IconButton(
                            icon: const Icon(Icons.remove_circle_outline),
                            onPressed: () => ref
                                .read(cartControllerProvider.notifier)
                                .setQuantity(
                                  line.product.id,
                                  line.quantity - 1,
                                ),
                          ),
                          Text('${line.quantity}'),
                          IconButton(
                            icon: const Icon(Icons.add_circle_outline),
                            onPressed: () => ref
                                .read(cartControllerProvider.notifier)
                                .setQuantity(
                                  line.product.id,
                                  line.quantity + 1,
                                ),
                          ),
                          Text(formatCents(line.lineTotalCents)),
                          IconButton(
                            icon: const Icon(Icons.close),
                            onPressed: () => ref
                                .read(cartControllerProvider.notifier)
                                .removeLine(line.product.id),
                          ),
                        ],
                      ),
                    );
                  },
                ),
        ),
        Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              Text(
                'Total: ${formatCents(cart.subtotalCents)}',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const Spacer(),
              FilledButton(
                onPressed: canCheckout ? null : () => _checkout(context),
                child: const Text('Checkout'),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Future<void> _pickCustomer(BuildContext context) async {
    final customer = await showModalBottomSheet<Customer>(
      context: context,
      isScrollControlled: true,
      builder: (_) => const CustomerPickerSheet(),
    );
    if (customer != null) {
      ref.read(cartControllerProvider.notifier).setCustomer(customer);
    }
  }

  Future<void> _openDrawer(BuildContext context) async {
    final opened = await showDialog<bool>(
      context: context,
      builder: (_) => const _OpenDrawerDialog(),
    );
    if (opened == true) {
      ref.read(cartControllerProvider.notifier).clear();
    }
  }

  Future<void> _checkout(BuildContext context) async {
    final result = await showModalBottomSheet<Order>(
      context: context,
      isScrollControlled: true,
      builder: (_) => const CheckoutSheet(),
    );
    if (result != null) {
      ref.read(cartControllerProvider.notifier).clear();
      if (!context.mounted) return;
      await Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => ReceiptScreen(orderId: result.id)),
      );
    }
  }
}

class CustomerPickerSheet extends ConsumerStatefulWidget {
  const CustomerPickerSheet({super.key});

  @override
  ConsumerState<CustomerPickerSheet> createState() =>
      _CustomerPickerSheetState();
}

class _CustomerPickerSheetState extends ConsumerState<CustomerPickerSheet> {
  late Future<List<Customer>> _future;

  @override
  void initState() {
    super.initState();
    _future = ref.read(customerRepositoryProvider).list();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
      ),
      child: FutureBuilder<List<Customer>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const SizedBox(
              height: 200,
              child: Center(child: CircularProgressIndicator()),
            );
          }
          final customers = snapshot.data ?? [];
          return ListView(
            shrinkWrap: true,
            children: [
              const ListTile(title: Text('Select customer')),
              for (final c in customers)
                ListTile(
                  title: Text(c.name),
                  subtitle: Text(c.email ?? ''),
                  trailing: Text('${c.pointsBalance} pts'),
                  onTap: () => Navigator.of(context).pop(c),
                ),
            ],
          );
        },
      ),
    );
  }
}

class _OpenDrawerDialog extends ConsumerStatefulWidget {
  const _OpenDrawerDialog();

  @override
  ConsumerState<_OpenDrawerDialog> createState() => _OpenDrawerDialogState();
}

class _OpenDrawerDialogState extends ConsumerState<_OpenDrawerDialog> {
  final _controller = TextEditingController(text: '0');
  bool _submitting = false;
  String? _error;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Open drawer'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextField(
            controller: _controller,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(
              labelText: 'Starting cash',
              prefixText: r'$ ',
              border: OutlineInputBorder(),
            ),
          ),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text(
                _error!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(false),
          child: const Text('Cancel'),
        ),
        FilledButton(
          onPressed: _submitting
              ? null
              : () async {
                  setState(() {
                    _submitting = true;
                    _error = null;
                  });
                  final cents = (double.tryParse(_controller.text) ?? 0) * 100;
                  try {
                    await ref
                        .read(drawerControllerProvider.notifier)
                        .open(startingCashCents: cents.round());
                    if (mounted && context.mounted) {
                      Navigator.of(context).pop(true);
                    }
                  } catch (e) {
                    if (mounted) setState(() => _error = e.toString());
                  } finally {
                    if (mounted) setState(() => _submitting = false);
                  }
                },
          child: const Text('Open'),
        ),
      ],
    );
  }
}
