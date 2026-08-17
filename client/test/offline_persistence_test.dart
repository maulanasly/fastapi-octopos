import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/api_client.dart';
import 'package:octopos_client/core/api_repositories.dart';
import 'package:octopos_client/core/local_persistence.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/core/token_store.dart';
import 'package:octopos_client/features/pos/cart_controller.dart';
import 'package:octopos_client/features/pos/catalog_controller.dart';
import 'package:shared_preferences/shared_preferences.dart';

Product _product(int id, {int stock = 10, double price = 5.0}) => Product(
  id: id,
  name: 'P$id',
  sku: 'S$id',
  price: price,
  stockQuantity: stock,
  minStock: 0,
  reorderPoint: 0,
  leadTimeDays: 0,
);

class _FakeCustomers extends CustomerRepository {
  _FakeCustomers(super.api);

  @override
  Future<List<Customer>> list() async => const [
    Customer(id: 7, name: 'Alice', isActive: true, pointsBalance: 3),
  ];
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('LocalStore cart persistence', () {
    test('save/load round-trips quantities and metadata', () async {
      SharedPreferences.setMockInitialValues({});
      final store = LocalStore();
      await store.saveCart(
        const PersistedCart(
          quantities: {1: 2, 3: 1},
          customerId: 7,
          promotionCode: 'SAVE10',
          redeemPoints: 5,
        ),
      );

      final loaded = await store.loadCart();
      expect(loaded, isNotNull);
      expect(loaded!.quantities, {1: 2, 3: 1});
      expect(loaded.customerId, 7);
      expect(loaded.promotionCode, 'SAVE10');
      expect(loaded.redeemPoints, 5);

      await store.clearCart();
      expect(await store.loadCart(), isNull);
    });

    test('invalid persisted data loads as null', () async {
      SharedPreferences.setMockInitialValues({'octopos_cart': 'not-json'});
      expect(await LocalStore().loadCart(), isNull);
    });

    test('watermark round-trips', () async {
      SharedPreferences.setMockInitialValues({});
      final store = LocalStore();
      expect(await store.readWatermark(), isNull);
      await store.writeWatermark('2026-08-16T10:00:00');
      expect(await store.readWatermark(), '2026-08-16T10:00:00');
    });
  });

  group('cart controller persistence', () {
    test('mutations persist the draft and clear removes it', () async {
      SharedPreferences.setMockInitialValues({});
      final container = ProviderContainer();
      addTearDown(container.dispose);
      final controller = container.read(cartControllerProvider.notifier);

      controller.addProduct(_product(1));
      controller.setQuantity(1, 2);

      final persisted = await container.read(localStoreProvider).loadCart();
      expect(persisted!.quantities, {1: 2});

      controller.clear();
      expect(await container.read(localStoreProvider).loadCart(), isNull);
    });

    test('restore rebuilds the cart from the persisted draft', () async {
      SharedPreferences.setMockInitialValues({});
      final container = ProviderContainer(
        overrides: [
          customerRepositoryProvider.overrideWithValue(
            _FakeCustomers(
              ApiClient(store: TokenStore(), onSessionExpired: () {}),
            ),
          ),
        ],
      );
      addTearDown(container.dispose);

      await container
          .read(localStoreProvider)
          .saveCart(
            const PersistedCart(quantities: {1: 2, 9: 1}, customerId: 7),
          );

      final controller = container.read(cartControllerProvider.notifier);
      await controller.restoreFromStorage([_product(1), _product(9)]);

      final state = container.read(cartControllerProvider);
      expect(state.lines[1]!.quantity, 2);
      expect(state.lines[9]!.quantity, 1);
      expect(state.customer?.id, 7);
      // draft cleared after restore
      expect(await container.read(localStoreProvider).loadCart(), isNull);
    });

    test('restore skips products missing from the catalog', () async {
      SharedPreferences.setMockInitialValues({});
      final container = ProviderContainer();
      addTearDown(container.dispose);

      await container
          .read(localStoreProvider)
          .saveCart(const PersistedCart(quantities: {1: 2, 99: 1}));

      final controller = container.read(cartControllerProvider.notifier);
      await controller.restoreFromStorage([_product(1)]);

      final state = container.read(cartControllerProvider);
      expect(state.lines.keys, [1]);
    });
  });

  group('catalog delta-aware load', () {
    test('first load stores the watermark and full catalog', () async {
      SharedPreferences.setMockInitialValues({});
      final container = ProviderContainer(
        overrides: [syncRepositoryProvider.overrideWithValue(_FakeSyncRepo())],
      );
      addTearDown(container.dispose);

      container.listen(catalogControllerProvider, (_, __) {});
      await Future<void>.delayed(const Duration(milliseconds: 20));

      final state = container.read(catalogControllerProvider);
      expect(state.products.length, 2);
      expect(state.loading, isFalse);
      expect(
        await container.read(localStoreProvider).readWatermark(),
        '2026-08-16T10:00:00',
      );
    });

    test('refresh merges the delta into the cache', () async {
      SharedPreferences.setMockInitialValues({});
      final fake = _FakeSyncRepo();
      final container = ProviderContainer(
        overrides: [syncRepositoryProvider.overrideWithValue(fake)],
      );
      addTearDown(container.dispose);

      container.listen(catalogControllerProvider, (_, __) {});
      await Future<void>.delayed(const Duration(milliseconds: 20));
      expect(container.read(catalogControllerProvider).products.length, 2);

      // mark a product changed and add one via the delta
      fake.delta = const CatalogDelta(
        serverTime: '2026-08-16T11:00:00',
        categories: [],
        products: [
          Product(
            id: 1,
            name: 'P1 Updated',
            sku: 'S1',
            price: 5,
            stockQuantity: 3,
            minStock: 0,
            reorderPoint: 0,
            leadTimeDays: 0,
          ),
          Product(
            id: 3,
            name: 'P3 New',
            sku: 'S3',
            price: 9,
            stockQuantity: 4,
            minStock: 0,
            reorderPoint: 0,
            leadTimeDays: 0,
          ),
        ],
      );

      await container.read(catalogControllerProvider.notifier).refresh();
      final state = container.read(catalogControllerProvider);
      final byId = {for (final p in state.products) p.id: p};
      expect(byId[1]!.name, 'P1 Updated');
      expect(byId[1]!.stockQuantity, 3);
      expect(byId[3]!.name, 'P3 New');
      expect(byId[2]!.name, 'P2', reason: 'unchanged product kept');
      expect(state.products.length, 3);
    });
  });
}

class _FakeSyncRepo extends SyncRepository {
  _FakeSyncRepo()
    : super(ApiClient(store: TokenStore(), onSessionExpired: () {}));

  CatalogDelta delta = const CatalogDelta(
    serverTime: '2026-08-16T10:00:00',
    categories: [],
    products: [
      Product(
        id: 1,
        name: 'P1',
        sku: 'S1',
        price: 5,
        stockQuantity: 10,
        minStock: 0,
        reorderPoint: 0,
        leadTimeDays: 0,
      ),
      Product(
        id: 2,
        name: 'P2',
        sku: 'S2',
        price: 6,
        stockQuantity: 10,
        minStock: 0,
        reorderPoint: 0,
        leadTimeDays: 0,
      ),
    ],
  );

  @override
  Future<CatalogDelta> catalog({String? since}) async {
    if (since == null) return delta;
    return delta;
  }
}
