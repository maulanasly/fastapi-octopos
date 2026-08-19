import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/api_client.dart';
import 'package:octopos_client/core/api_repositories.dart';
import 'package:octopos_client/core/auth_controller.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/core/token_store.dart';
import 'package:octopos_client/features/purchasing/purchasing_screen.dart';

class _FixedLanguageLocalization extends LocalizationController {
  @override
  LocalizationState build() => const LocalizationState(
    setting: LocalizationSetting(
      language: 'en',
      timezone: 'UTC',
      currency: 'USD',
      dateFormat: '%Y-%m-%d %H:%M:%S',
      numberFormat: 'en_US',
      countryCode: 'US',
    ),
  );
}

class _FakeAuth extends AuthController {
  @override
  AuthState build() => const AuthState(
    status: AuthStatus.signedIn,
    userId: 1,
    email: 'manager@example.com',
    permissions: {'purchasing:manage', 'purchasing:approve'},
  );
}

class _FakePurchasing extends PurchasingRepository {
  _FakePurchasing()
    : super(ApiClient(store: TokenStore(), onSessionExpired: () {}));

  int submitOrderCalls = 0;
  int markOrderedCalls = 0;
  int submitPaymentCalls = 0;
  int createPaymentCalls = 0;

  @override
  Future<List<Supplier>> suppliers() async => const [
    Supplier(
      id: 1,
      name: 'Acme Supply',
      contactEmail: 'orders@acme.test',
      phone: '+1-555-0100',
      isActive: true,
    ),
  ];

  @override
  Future<List<PurchaseOrder>> orders({String? status, int limit = 100}) async {
    return const [
      PurchaseOrder(
        id: 11,
        supplierId: 1,
        userId: 1,
        status: 'draft',
        totalEstimatedAmount: 150.0,
        createdAt: '2026-08-17T10:00:00',
        items: [
          PurchaseOrderItem(
            id: 21,
            purchaseOrderId: 11,
            productId: 3,
            quantityOrdered: 10,
            quantityReceived: 0,
            unitCost: 15.0,
          ),
        ],
      ),
    ];
  }

  @override
  Future<List<PurchaseInvoice>> invoices({String? status, int limit = 100}) async {
    return const [
      PurchaseInvoice(
        id: 31,
        supplierId: 1,
        purchaseOrderId: 11,
        userId: 1,
        invoiceNumber: 'INV-001',
        status: 'pending_review',
        subtotalAmount: 150.0,
        totalAmount: 150.0,
        varianceAmount: 0,
        hasQuantityVariance: false,
        hasPriceVariance: false,
        items: [],
      ),
    ];
  }

  @override
  Future<List<SupplierPayment>> payments({
    String? status,
    int limit = 100,
  }) async {
    return const [
      SupplierPayment(
        id: 41,
        supplierId: 1,
        invoiceId: 31,
        userId: 1,
        amount: 100.0,
        paymentMethod: 'cash',
        status: 'pending_review',
      ),
    ];
  }

  @override
  Future<PurchaseOrder> submitOrder(
    int purchaseOrderId, {
    String? reviewNote,
  }) async {
    submitOrderCalls++;
    return const PurchaseOrder(
      id: 11,
      supplierId: 1,
      userId: 1,
      status: 'pending_review',
      totalEstimatedAmount: 150.0,
      items: [],
    );
  }

  @override
  Future<PurchaseOrder> markOrdered(int purchaseOrderId) async {
    markOrderedCalls++;
    return const PurchaseOrder(
      id: 11,
      supplierId: 1,
      userId: 1,
      status: 'ordered',
      totalEstimatedAmount: 150.0,
      items: [],
    );
  }

  @override
  Future<SupplierPayment> submitPayment(
    int paymentId, {
    String? reviewNote,
  }) async {
    submitPaymentCalls++;
    return const SupplierPayment(
      id: 41,
      supplierId: 1,
      invoiceId: 31,
      userId: 1,
      amount: 100.0,
      paymentMethod: 'cash',
      status: 'pending_review',
    );
  }

  @override
  Future<SupplierPayment> createPayment(Map<String, dynamic> body) async {
    createPaymentCalls++;
    return const SupplierPayment(
      id: 41,
      supplierId: 1,
      invoiceId: 31,
      userId: 1,
      amount: 100.0,
      paymentMethod: 'cash',
      status: 'draft',
    );
  }
}

ProviderContainer _container() => ProviderContainer(
  overrides: [
    localizationControllerProvider.overrideWith(_FixedLanguageLocalization.new),
    authControllerProvider.overrideWith(_FakeAuth.new),
    purchasingRepositoryProvider.overrideWithValue(_FakePurchasing()),
  ],
);

Future<void> _pump(WidgetTester tester, ProviderContainer container) async {
  await tester.pumpWidget(
    UncontrolledProviderScope(
      container: container,
      child: const MaterialApp(home: PurchasingScreen()),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('suppliers tab lists active suppliers', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pump(tester, container);

    expect(find.text('Acme Supply'), findsOneWidget);
    expect(find.textContaining('orders@acme.test'), findsOneWidget);
  });

  testWidgets('purchase orders tab shows draft PO with status', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pump(tester, container);

    await tester.tap(find.text('Purchase orders'));
    await tester.pumpAndSettle();

    expect(find.text('PO #11 · draft'), findsOneWidget);
  });

  testWidgets('draft PO can be submitted for review', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    final fake = container.read(purchasingRepositoryProvider) as _FakePurchasing;
    await _pump(tester, container);

    await tester.tap(find.text('Purchase orders'));
    await tester.pumpAndSettle();

    await tester.tap(find.textContaining('PO #11'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Submit for review'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Submit for review').last);
    await tester.pumpAndSettle();

    expect(fake.submitOrderCalls, 1);
    expect(fake.markOrderedCalls, 0);
  });

  testWidgets('invoices tab shows pending review invoice', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pump(tester, container);

    await tester.tap(find.text('Purchase invoices'));
    await tester.pumpAndSettle();

    expect(find.text('INV-001 · pending_review'), findsOneWidget);
  });

  testWidgets('payments tab lists pending payment', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pump(tester, container);

    await tester.tap(find.text('Supplier payments'));
    await tester.pumpAndSettle();

    expect(find.text('#41 · pending_review'), findsOneWidget);
    expect(find.textContaining('100.00'), findsOneWidget);
  });

  testWidgets('pending payment can be submitted', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    final fake = container.read(purchasingRepositoryProvider) as _FakePurchasing;
    await _pump(tester, container);

    await tester.tap(find.text('Supplier payments'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('#41 · pending_review'));
    await tester.pumpAndSettle();
    expect(find.text('Approve'), findsOneWidget);

    await tester.tap(find.text('Approve'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Approve').last);
    await tester.pumpAndSettle();

    expect(fake.createPaymentCalls, 0);
  });

  testWidgets('create payment dialog requires approved invoice', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    final fake = container.read(purchasingRepositoryProvider) as _FakePurchasing;
    await _pump(tester, container);

    await tester.tap(find.text('Supplier payments'));
    await tester.pumpAndSettle();
    await tester.tap(find.byType(FloatingActionButton));
    await tester.pumpAndSettle();

    expect(find.text('Create payment'), findsWidgets);
    expect(find.text('Amount'), findsOneWidget);
    expect(fake.createPaymentCalls, 0);
  });
}
