/// Cashier POS screen: catalog grid + cart + checkout + receipt.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api_repositories.dart';
import '../../core/colors.dart';
import '../../core/config.dart';
import '../../core/strings.dart';
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
    final s = ref.watch(stringsProvider);
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
                child: Text(s.of('openDrawer')),
              ),
            ],
          )
        else if (drawer.session != null)
          MaterialBanner(
            content: Text(s.of('drawerOpen', args: {'id': drawer.session!.id})),
            leading: const Icon(Icons.lock_open),
            actions: [
              TextButton(
                onPressed: () => context.push('/reconcile'),
                child: Text(s.of('endShift')),
              ),
            ],
          ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8),
          child: Row(
            children: [
              TextButton.icon(
                icon: const Icon(Icons.assignment_return, size: 18),
                label: Text(s.of('refunds')),
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
    final s = ref.watch(stringsProvider);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.all(8),
          child: TextField(
            decoration: InputDecoration(
              hintText: s.of('searchProducts'),
              prefixIcon: const Icon(Icons.search),
              border: const OutlineInputBorder(),
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
                  label: Text(s.of('all')),
                  selected: _selectedCategoryId == null,
                  onSelected: (_) => setState(() => _selectedCategoryId = null),
                ),
              ),
              for (final category in catalog.categories)
                Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: _CategoryChip(
                    category: category,
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
    final s = ref.watch(stringsProvider);
    final outOfStock = product.stockQuantity <= 0;
    final categoryColor = colorFromHex(product.category?.color);
    final imageUrl = product.imageUrl;
    return Card(
      clipBehavior: Clip.antiAlias,
      color: outOfStock
          ? Theme.of(context).colorScheme.surfaceContainerHighest
          : null,
      child: InkWell(
        onTap: outOfStock
            ? null
            : () =>
                  ref.read(cartControllerProvider.notifier).addProduct(product),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              height: 4,
              color:
                  categoryColor ??
                  (outOfStock
                      ? Theme.of(context).colorScheme.surfaceContainerHighest
                      : Theme.of(context).colorScheme.outlineVariant),
            ),
            AspectRatio(
              aspectRatio: 4 / 3,
              child: imageUrl != null
                  ? Image.network(
                      '${AppConfig.mediaBaseUrl}$imageUrl',
                      fit: BoxFit.cover,
                      errorBuilder: (_, _, _) =>
                          _ProductMonogram(product: product),
                      loadingBuilder: (context, child, progress) {
                        if (progress == null) return child;
                        return _ProductMonogram(
                          product: product,
                          showIcon: true,
                        );
                      },
                    )
                  : _ProductMonogram(product: product),
            ),
            // Fixed bottom label bar: the name is always visible and the
            // tile height stays uniform regardless of the image.
            Container(
              padding: const EdgeInsets.fromLTRB(8, 8, 8, 10),
              color: categoryColor != null
                  ? softBackground(categoryColor)
                  : Theme.of(context).colorScheme.surfaceContainerLow,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    product.name,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      color: categoryColor != null
                          ? textColorOn(softBackground(categoryColor))
                          : null,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    formatCents(product.priceCents),
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: Theme.of(context).colorScheme.primary,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Text(
                    s.of('inStock', args: {'count': product.stockQuantity}),
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: outOfStock
                          ? Theme.of(context).colorScheme.error
                          : Colors.grey,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _cartPane(BuildContext context, CartState cart) {
    final s = ref.watch(stringsProvider);
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
                RawChip(
                  label: Text(
                    cart.customer!.name,
                    overflow: TextOverflow.ellipsis,
                  ),
                  onPressed: () => _pickCustomer(context),
                  onDeleted: () => ref
                      .read(cartControllerProvider.notifier)
                      .setCustomer(null),
                )
              else
                ActionChip(
                  avatar: const Icon(Icons.person_off_outlined, size: 16),
                  label: Text(s.of('guest')),
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
                child: Text(s.of('checkout')),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Future<void> _pickCustomer(BuildContext context) async {
    final result = await showDialog<_CustomerPickResult>(
      context: context,
      builder: (_) => const CustomerPickerDialog(),
    );
    if (result != null) {
      ref.read(cartControllerProvider.notifier).setCustomer(result.customer);
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

/// Result of the customer picker: [customer] is null for walk-in guests.
class _CustomerPickResult {
  const _CustomerPickResult(this.customer);

  final Customer? customer;
}

/// Centered customer picker: walk-in guest, search, register, select.
class CustomerPickerDialog extends ConsumerStatefulWidget {
  const CustomerPickerDialog({super.key});

  @override
  ConsumerState<CustomerPickerDialog> createState() =>
      _CustomerPickerDialogState();
}

class _CustomerPickerDialogState extends ConsumerState<CustomerPickerDialog> {
  late Future<List<Customer>> _future;
  String _query = '';

  @override
  void initState() {
    super.initState();
    _future = ref.read(customerRepositoryProvider).list();
  }

  Future<void> _register() async {
    final s = ref.read(stringsProvider);
    final name = TextEditingController();
    final email = TextEditingController();
    final phone = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(s.of('registerCustomer')),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: name,
              decoration: InputDecoration(labelText: s.of('name')),
            ),
            TextField(
              controller: email,
              decoration: InputDecoration(labelText: s.of('email')),
            ),
            TextField(
              controller: phone,
              decoration: InputDecoration(labelText: s.of('phone')),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text(s.of('cancel')),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: Text(s.of('create')),
          ),
        ],
      ),
    );
    if (ok != true) return;
    final customer = await ref
        .read(customerRepositoryProvider)
        .create(
          name: name.text.trim(),
          email: email.text.trim().isEmpty ? null : email.text.trim(),
          phone: phone.text.trim().isEmpty ? null : phone.text.trim(),
        );
    if (mounted) Navigator.of(context).pop(_CustomerPickResult(customer));
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    return Dialog(
      child: ConstrainedBox(
        constraints: BoxConstraints(
          maxWidth: 480,
          maxHeight: MediaQuery.of(context).size.height * 0.6,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
              child: Text(
                s.of('selectCustomer'),
                style: Theme.of(context).textTheme.titleMedium,
              ),
            ),
            ListTile(
              leading: const Icon(Icons.person_off_outlined),
              title: Text(s.of('walkInGuest')),
              onTap: () =>
                  Navigator.of(context).pop(const _CustomerPickResult(null)),
            ),
            const Divider(height: 1),
            Padding(
              padding: const EdgeInsets.all(12),
              child: TextField(
                decoration: InputDecoration(
                  hintText: s.of('searchProducts'),
                  prefixIcon: const Icon(Icons.search),
                  isDense: true,
                ),
                onChanged: (v) =>
                    setState(() => _query = v.trim().toLowerCase()),
              ),
            ),
            Expanded(
              child: FutureBuilder<List<Customer>>(
                future: _future,
                builder: (context, snapshot) {
                  if (snapshot.connectionState != ConnectionState.done) {
                    return const Center(child: CircularProgressIndicator());
                  }
                  final all = snapshot.data ?? [];
                  final customers = _query.isEmpty
                      ? all
                      : all
                            .where(
                              (c) =>
                                  c.name.toLowerCase().contains(_query) ||
                                  (c.email ?? '').toLowerCase().contains(
                                    _query,
                                  ) ||
                                  (c.phone ?? '').toLowerCase().contains(
                                    _query,
                                  ),
                            )
                            .toList();
                  if (customers.isEmpty) {
                    return Center(child: Text(s.of('noCustomersFound')));
                  }
                  return ListView.builder(
                    itemCount: customers.length,
                    itemBuilder: (context, i) {
                      final c = customers[i];
                      return ListTile(
                        dense: true,
                        title: Text(c.name),
                        subtitle: Text(c.email ?? ''),
                        trailing: Text('${c.pointsBalance} pts'),
                        onTap: () =>
                            Navigator.of(context).pop(_CustomerPickResult(c)),
                      );
                    },
                  );
                },
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(8),
              child: OutlinedButton.icon(
                icon: const Icon(Icons.person_add_alt, size: 18),
                label: Text(s.of('registerCustomer')),
                onPressed: _register,
              ),
            ),
          ],
        ),
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
          child: Text(ref.read(stringsProvider).of('cancel')),
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
          child: Text(ref.read(stringsProvider).of('openDrawer')),
        ),
      ],
    );
  }
}

/// Category chip tinted with the category's configured color.
class _CategoryChip extends StatelessWidget {
  const _CategoryChip({
    required this.category,
    required this.selected,
    required this.onSelected,
  });

  final Category category;
  final bool selected;
  final ValueChanged<bool> onSelected;

  @override
  Widget build(BuildContext context) {
    final color = colorFromHex(category.color);
    if (color == null) {
      return ChoiceChip(
        label: Text(category.name),
        selected: selected,
        onSelected: onSelected,
      );
    }
    return ChoiceChip(
      label: Text(category.name, style: TextStyle(color: textColorOn(color))),
      selected: selected,
      onSelected: onSelected,
      backgroundColor: softBackground(color),
      selectedColor: color,
      checkmarkColor: textColorOn(color),
      side: BorderSide(color: selected ? color : color.withValues(alpha: 0.4)),
    );
  }
}

/// Monogram fallback (category-colored) for products without an image.
class _ProductMonogram extends StatelessWidget {
  const _ProductMonogram({required this.product, this.showIcon = false});

  final Product product;
  final bool showIcon;

  @override
  Widget build(BuildContext context) {
    final color =
        colorFromHex(product.category?.color) ??
        Theme.of(context).colorScheme.surfaceContainerHighest;
    return Container(
      color: color,
      alignment: Alignment.center,
      child: showIcon
          ? Icon(
              Icons.image_outlined,
              size: 32,
              color: textColorOn(color).withValues(alpha: 0.6),
            )
          : Text(
              product.name.isEmpty ? '?' : product.name[0].toUpperCase(),
              style: TextStyle(
                fontSize: 32,
                fontWeight: FontWeight.bold,
                color: textColorOn(color),
              ),
            ),
    );
  }
}
