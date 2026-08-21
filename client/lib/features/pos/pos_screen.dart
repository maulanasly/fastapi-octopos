/// Cashier POS screen: catalog grid + cart + checkout + receipt.
library;

import 'package:flutter/foundation.dart' show defaultTargetPlatform, kIsWeb;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api_repositories.dart';
import '../../core/async_views.dart';
import '../../core/auth_controller.dart';
import '../../core/colors.dart';
import '../../core/errors.dart';
import '../../core/money.dart';
import '../../core/models.dart';
import '../../core/strings.dart';
import '../drawer/drawer_controller.dart';
import 'product_tile.dart';
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
  final _searchFocus = FocusNode();

  /// Soft keyboards should not cover half the grid on touch devices just
  /// because the screen opened; hardware-keyboard platforms (and the
  /// barcode scanners attached to them) get the autofocus.
  bool get _hardwareKeyboard =>
      !kIsWeb &&
      const {
        TargetPlatform.linux,
        TargetPlatform.windows,
        TargetPlatform.macOS,
      }.contains(defaultTargetPlatform);

  @override
  void dispose() {
    _searchFocus.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    final auth = ref.watch(authControllerProvider);
    final catalog = ref.watch(catalogControllerProvider);
    final cart = ref.watch(cartControllerProvider);
    final drawer = ref.watch(drawerControllerProvider);
    // Restore the persisted draft once the catalog is available.
    ref.watch(cartRestoreProvider);

    final products = _filtered(catalog.products);

    return Column(
      children: [
        if (drawer.session == null && !drawer.loading)
          MaterialBanner(
            content: Text(s.of('noOpenDrawerBanner')),
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
              if (auth.has('refunds:create'))
                TextButton.icon(
                  icon: const Icon(Icons.assignment_return, size: 18),
                  label: Text(s.of('refunds')),
                  onPressed: () => context.push('/refunds'),
                ),
              const Spacer(),
              IconButton(
                tooltip: s.of('refreshCatalog'),
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
              Expanded(flex: 2, child: _cartPane(context, cart, drawer)),
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
            focusNode: _searchFocus,
            autofocus: _hardwareKeyboard,
            textInputAction: TextInputAction.search,
            decoration: InputDecoration(
              hintText: s.of('searchProducts'),
              prefixIcon: const Icon(Icons.search),
              // Touch devices: explicit focus button so the soft keyboard
              // only appears when the cashier asks for it.
              suffixIcon: _hardwareKeyboard
                  ? null
                  : IconButton(
                      tooltip: s.of('searchProducts'),
                      icon: const Icon(Icons.keyboard),
                      onPressed: () => _searchFocus.requestFocus(),
                    ),
              border: const OutlineInputBorder(),
              isDense: true,
            ),
            onChanged: (v) => setState(() => _search = v),
            // Barcode scanners type into the focused field and send Enter:
            // add the best match to the cart, with audible/haptic feedback.
            onSubmitted: (_) {
              final matches = _filtered(catalog.products);
              if (matches.isEmpty) {
                ScaffoldMessenger.of(context)
                    .showSnackBar(SnackBar(content: Text(s.of('scanNoMatch'))));
                return;
              }
              HapticFeedback.selectionClick();
              ref
                  .read(cartControllerProvider.notifier)
                  .addProduct(matches.first);
              _searchFocus.requestFocus();
            },
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
              ? ErrorStateView(
                  message: s.of('genericError'),
                  onRetry: () =>
                      ref.read(catalogControllerProvider.notifier).refresh(),
                )
              : RefreshIndicator(
                  onRefresh: () =>
                      ref.read(catalogControllerProvider.notifier).refresh(),
                  child: GridView.builder(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(8),
                    gridDelegate:
                        const SliverGridDelegateWithMaxCrossAxisExtent(
                          maxCrossAxisExtent: 200,
                          childAspectRatio: 0.9,
                          mainAxisSpacing: 8,
                          crossAxisSpacing: 8,
                        ),
                    itemCount: products.length,
                    itemBuilder: (context, i) => ProductTile(
                      product: products[i],
                      onTap: () => ref
                          .read(cartControllerProvider.notifier)
                          .addProduct(products[i]),
                    ),
                  ),
                ),
        ),
      ],
    );
  }

  Widget _cartPane(BuildContext context, CartState cart, DrawerState drawer) {
    final s = ref.watch(stringsProvider);
    final noDrawer = drawer.session == null;
    final canCheckout = cart.isEmpty || noDrawer;
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              Text(
                s.of('cartCount', args: {'count': cart.itemCount}),
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
              ? EmptyStateView(
                  message: s.of('cartEmpty'),
                  icon: Icons.shopping_cart_outlined,
                )
              : ListView.separated(
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  itemCount: cart.lines.length,
                  separatorBuilder: (_, _) => const Divider(height: 8),
                  itemBuilder: (context, i) {
                    final line = cart.lines.values.elementAt(i);
                    return ListTile(
                      dense: true,
                      title: Text(line.product.name),
                      // Unit × qty = line total, so the trailing row only
                      // carries controls and can never overflow.
                      subtitle: Text(
                        '${formatCents(line.product.priceCents)} × '
                        '${line.quantity} = ${formatCents(line.lineTotalCents)}',
                      ),
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          IconButton(
                            tooltip: s.of('decreaseQty'),
                            icon: const Icon(Icons.remove_circle_outline),
                            onPressed: () => ref
                                .read(cartControllerProvider.notifier)
                                .setQuantity(
                                  line.product.id,
                                  line.quantity - 1,
                                ),
                          ),
                          ConstrainedBox(
                            constraints: const BoxConstraints(minWidth: 28),
                            child: Text(
                              '${line.quantity}',
                              textAlign: TextAlign.center,
                            ),
                          ),
                          IconButton(
                            tooltip: s.of('increaseQty'),
                            icon: const Icon(Icons.add_circle_outline),
                            onPressed: () => ref
                                .read(cartControllerProvider.notifier)
                                .setQuantity(
                                  line.product.id,
                                  line.quantity + 1,
                                ),
                          ),
                          IconButton(
                            tooltip: s.of('removeLine'),
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
              // Flexible: long totals must shrink, not push the checkout
              // button off-pane on narrower windows.
              Expanded(
                child: Text(
                  '${s.of('total')}: ${formatCents(cart.subtotalCents)}',
                  style: Theme.of(context).textTheme.titleLarge,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              const SizedBox(width: 8),
              FilledButton(
                onPressed: canCheckout ? null : () => _checkout(context),
                // Say WHY the button is disabled instead of leaving a
                // mysteriously dead button on the busiest screen.
                child: Text(
                  noDrawer && !cart.isEmpty
                      ? s.of('needDrawer')
                      : s.of('checkout'),
                ),
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
    await showDialog<bool>(
      context: context,
      builder: (_) => const _OpenDrawerDialog(),
    );
    // NOTE: intentionally no cart.clear() here — the draft belongs to the
    // cashier, not the drawer session; wiping it on open destroyed work.
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
    final customer = await showDialog<Customer>(
      context: context,
      builder: (_) => const _CustomerRegisterDialog(),
    );
    if (customer != null && mounted) {
      Navigator.of(context).pop(_CustomerPickResult(customer));
    }
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
                  hintText: s.of('searchCustomers'),
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
                        trailing: Text(
                          '${c.pointsBalance} ${s.of('pointsUnit')}',
                        ),
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

/// Register-customer dialog. Owns its controllers in State so they are
/// disposed exactly when the dialog leaves the tree (a plain helper method
/// would dispose them while the exit transition still reads them).
class _CustomerRegisterDialog extends ConsumerStatefulWidget {
  const _CustomerRegisterDialog();

  @override
  ConsumerState<_CustomerRegisterDialog> createState() =>
      _CustomerRegisterDialogState();
}

class _CustomerRegisterDialogState
    extends ConsumerState<_CustomerRegisterDialog> {
  final _formKey = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _phone = TextEditingController();
  bool _submitting = false;

  @override
  void dispose() {
    _name.dispose();
    _email.dispose();
    _phone.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _submitting = true);
    try {
      final customer = await ref
          .read(customerRepositoryProvider)
          .create(
            name: _name.text.trim(),
            email: _email.text.trim().isEmpty ? null : _email.text.trim(),
            phone: _phone.text.trim().isEmpty ? null : _phone.text.trim(),
          );
      if (mounted) Navigator.of(context).pop(customer);
    } catch (_) {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    return AlertDialog(
      title: Text(s.of('registerCustomer')),
      content: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextFormField(
              controller: _name,
              autofocus: true,
              decoration: InputDecoration(labelText: s.of('name')),
              validator: (v) =>
                  (v == null || v.trim().isEmpty) ? s.of('required') : null,
            ),
            TextFormField(
              controller: _email,
              keyboardType: TextInputType.emailAddress,
              decoration: InputDecoration(labelText: s.of('email')),
              validator: (v) => (v != null && v.isNotEmpty && !v.contains('@'))
                  ? s.of('invalidEmail')
                  : null,
            ),
            TextFormField(
              controller: _phone,
              keyboardType: TextInputType.phone,
              decoration: InputDecoration(labelText: s.of('phone')),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: Text(s.of('cancel')),
        ),
        FilledButton(
          onPressed: _submitting ? null : _submit,
          child: _submitting
              ? const SizedBox(
                  height: 18,
                  width: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : Text(s.of('create')),
        ),
      ],
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
    final s = ref.watch(stringsProvider);
    return AlertDialog(
      title: Text(s.of('openDrawer')),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextField(
            controller: _controller,
            keyboardType: TextInputType.number,
            decoration: InputDecoration(
              labelText: s.of('startingCash'),
              prefixText: currencySymbol(currentCurrency),
              border: const OutlineInputBorder(),
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
          child: Text(s.of('cancel')),
        ),
        FilledButton(
          onPressed: _submitting
              ? null
              : () async {
                  setState(() {
                    _submitting = true;
                    _error = null;
                  });
                  try {
                    await ref
                        .read(drawerControllerProvider.notifier)
                        .open(
                          startingCashCents: centsFromInput(_controller.text),
                        );
                    if (mounted && context.mounted) {
                      Navigator.of(context).pop(true);
                    }
                  } catch (e) {
                    if (mounted) {
                      setState(() => _error = friendlyError(e, s));
                    }
                  } finally {
                    if (mounted) setState(() => _submitting = false);
                  }
                },
          child: Text(s.of('openDrawer')),
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
