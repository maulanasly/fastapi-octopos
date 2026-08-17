/// Cart state for the cashier screen, with draft persistence.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/local_persistence.dart';
import '../../core/models.dart';
import 'catalog_controller.dart';

final localStoreProvider = Provider<LocalStore>((ref) => LocalStore());

class CartLine {
  final Product product;
  int quantity;

  CartLine({required this.product, this.quantity = 1});

  int get lineTotalCents => product.priceCents * quantity;
}

class CartState {
  final Map<int, CartLine> lines;
  final Customer? customer;
  final String promotionCode;
  final int redeemPoints;

  const CartState({
    this.lines = const {},
    this.customer,
    this.promotionCode = '',
    this.redeemPoints = 0,
  });

  int get subtotalCents =>
      lines.values.fold(0, (sum, line) => sum + line.lineTotalCents);

  int get itemCount => lines.values.fold(0, (sum, line) => sum + line.quantity);

  bool get isEmpty => lines.isEmpty;

  CartState copyWith({
    Map<int, CartLine>? lines,
    Customer? customer,
    String? promotionCode,
    int? redeemPoints,
  }) => CartState(
    lines: lines ?? this.lines,
    customer: customer ?? this.customer,
    promotionCode: promotionCode ?? this.promotionCode,
    redeemPoints: redeemPoints ?? this.redeemPoints,
  );
}

class CartController extends Notifier<CartState> {
  bool _restored = false;

  @override
  CartState build() => const CartState();

  /// Restores the persisted draft once, when the catalog is available to
  /// resolve products.
  Future<void> restoreFromStorage(List<Product> catalogProducts) async {
    if (_restored) return;
    _restored = true;
    final persisted = await ref.read(localStoreProvider).loadCart();
    if (persisted == null) return;

    final byId = {for (final p in catalogProducts) p.id: p};
    final lines = <int, CartLine>{};
    for (final entry in persisted.quantities.entries) {
      final product = byId[entry.key];
      if (product == null || product.stockQuantity <= 0) continue;
      lines[entry.key] = CartLine(
        product: product,
        quantity: entry.value.clamp(1, product.stockQuantity),
      );
    }
    if (lines.isEmpty) {
      await ref.read(localStoreProvider).clearCart();
      return;
    }

    Customer? customer;
    if (persisted.customerId != null) {
      try {
        final customers = await ref.read(customerRepositoryProvider).list();
        for (final c in customers) {
          if (c.id == persisted.customerId) customer = c;
        }
      } catch (_) {
        // Customer unavailable offline: keep the cart without it.
      }
    }

    state = CartState(
      lines: lines,
      customer: customer,
      promotionCode: persisted.promotionCode,
      redeemPoints: persisted.redeemPoints,
    );
    await ref.read(localStoreProvider).clearCart();
  }

  void addProduct(Product product) {
    final lines = Map<int, CartLine>.from(state.lines);
    final existing = lines[product.id];
    if (existing != null) {
      if (existing.quantity < product.stockQuantity) {
        existing.quantity += 1;
      }
    } else {
      if (product.stockQuantity > 0) {
        lines[product.id] = CartLine(product: product);
      }
    }
    state = state.copyWith(lines: lines);
    _persist();
  }

  void setQuantity(int productId, int quantity) {
    final lines = Map<int, CartLine>.from(state.lines);
    final line = lines[productId];
    if (line == null) return;
    if (quantity <= 0) {
      lines.remove(productId);
    } else {
      final max = line.product.stockQuantity;
      line.quantity = quantity > max ? max : quantity;
    }
    state = state.copyWith(lines: lines);
    _persist();
  }

  void removeLine(int productId) {
    final lines = Map<int, CartLine>.from(state.lines)..remove(productId);
    state = state.copyWith(lines: lines);
    _persist();
  }

  void setCustomer(Customer? customer) {
    state = state.copyWith(customer: customer);
    _persist();
  }

  void setPromotionCode(String code) {
    state = state.copyWith(promotionCode: code);
    _persist();
  }

  void setRedeemPoints(int points) {
    state = state.copyWith(redeemPoints: points);
    _persist();
  }

  void clear() {
    state = const CartState();
    ref.read(localStoreProvider).clearCart();
  }

  void _persist() {
    if (state.isEmpty) {
      ref.read(localStoreProvider).clearCart();
      return;
    }
    ref
        .read(localStoreProvider)
        .saveCart(
          PersistedCart(
            quantities: {
              for (final entry in state.lines.entries)
                entry.key: entry.value.quantity,
            },
            customerId: state.customer?.id,
            promotionCode: state.promotionCode,
            redeemPoints: state.redeemPoints,
          ),
        );
  }

  /// Builds the /orders item payload.
  List<Map<String, dynamic>> orderItems() => [
    for (final line in state.lines.values)
      {'product_id': line.product.id, 'quantity': line.quantity},
  ];
}

final cartControllerProvider = NotifierProvider<CartController, CartState>(
  CartController.new,
);

/// Restores the persisted draft once the catalog has loaded.
final cartRestoreProvider = Provider<void>((ref) {
  final catalog = ref.watch(catalogControllerProvider);
  if (catalog.loading || catalog.products.isEmpty) return;
  ref
      .read(cartControllerProvider.notifier)
      .restoreFromStorage(catalog.products);
});
