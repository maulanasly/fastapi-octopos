import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/features/pos/cart_controller.dart';

Product _product(int id, {double price = 10.0, int stock = 10}) => Product(
  id: id,
  name: 'Product $id',
  sku: 'SKU-$id',
  price: price,
  stockQuantity: stock,
  minStock: 0,
  reorderPoint: 0,
  leadTimeDays: 0,
);

void main() {
  late ProviderContainer container;
  late CartController controller;

  setUp(() {
    container = ProviderContainer();
    controller = container.read(cartControllerProvider.notifier);
  });

  tearDown(() => container.dispose());

  test('adds products and computes subtotal', () {
    controller.addProduct(_product(1, price: 4.50));
    controller.addProduct(_product(2, price: 3.25));
    controller.addProduct(_product(1, price: 4.50));

    final state = container.read(cartControllerProvider);
    expect(state.itemCount, 3);
    expect(state.subtotalCents, 1225); // 2*450 + 325
  });

  test('does not add out-of-stock products', () {
    controller.addProduct(_product(1, stock: 0));
    expect(container.read(cartControllerProvider).isEmpty, isTrue);
  });

  test('clamps quantity to available stock', () {
    controller.addProduct(_product(1, stock: 3));
    controller.setQuantity(1, 99);
    final state = container.read(cartControllerProvider);
    expect(state.lines[1]!.quantity, 3);
  });

  test('removes line when quantity drops to zero', () {
    controller.addProduct(_product(1));
    controller.setQuantity(1, 0);
    expect(container.read(cartControllerProvider).isEmpty, isTrue);
  });

  test('clears cart', () {
    controller.addProduct(_product(1));
    controller.clear();
    expect(container.read(cartControllerProvider).isEmpty, isTrue);
  });

  test('builds order item payload', () {
    controller.addProduct(_product(1));
    controller.addProduct(_product(2, stock: 5));
    controller.setQuantity(1, 2);

    final items = controller.orderItems();
    expect(
      items,
      containsAllInOrder([
        {'product_id': 1, 'quantity': 2},
        {'product_id': 2, 'quantity': 1},
      ]),
    );
  });

  test('tracks customer and promotion code', () {
    const customer = Customer(
      id: 7,
      name: 'Alice',
      isActive: true,
      pointsBalance: 12,
    );
    controller.setCustomer(customer);
    controller.setPromotionCode('SAVE10');

    final state = container.read(cartControllerProvider);
    expect(state.customer!.id, 7);
    expect(state.promotionCode, 'SAVE10');
  });
}
