/// Cart state for the cashier screen.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models.dart';

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
  @override
  CartState build() => const CartState();

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
  }

  void removeLine(int productId) {
    final lines = Map<int, CartLine>.from(state.lines)..remove(productId);
    state = state.copyWith(lines: lines);
  }

  void setCustomer(Customer? customer) =>
      state = state.copyWith(customer: customer);

  void setPromotionCode(String code) =>
      state = state.copyWith(promotionCode: code);

  void setRedeemPoints(int points) =>
      state = state.copyWith(redeemPoints: points);

  void clear() => state = const CartState();

  /// Builds the /orders item payload.
  List<Map<String, dynamic>> orderItems() => [
    for (final line in state.lines.values)
      {'product_id': line.product.id, 'quantity': line.quantity},
  ];
}

final cartControllerProvider = NotifierProvider<CartController, CartState>(
  CartController.new,
);
