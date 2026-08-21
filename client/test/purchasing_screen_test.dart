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
  _FakeAuth({this.ownerId = 1, this.isSuperuser = false});

  final int? ownerId;
  final bool isSuperuser;

  @override
  AuthState build() => AuthState(
    status: AuthStatus.signedIn,
    userId: ownerId,
    email: 'manager@example.com',
    permissions: {'purchasing:manage', 'purchasing:approve'},
    isSuperuser: isSuperuser,
  );
}

class _FakePurchasing extends PurchasingRepository {
  _FakePurchasing()
    : super(ApiClient(store: TokenStore(), onSessionExpired: () {}));

  int submitOrderCalls = 0;
  int markOrderedCalls = 0;
  int rejectOrderCalls = 0;
  int submitInvoiceCalls = 0;
  int approveInvoiceCalls = 0;
  int rejectInvoiceCalls = 0;
  int submitPaymentCalls = 0;
  int approvePaymentCalls = 0;
  int rejectPaymentCalls = 0;
  int createPaymentCalls = 0;

  String? lastOrderNote;
  String? lastInvoiceNote;
  String? lastPaymentNote;

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
        userId: 2,
        status: 'pending_review',
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
        userId: 2,
        invoiceNumber: 'INV-001',
        status: 'pending_review',
        subtotalAmount: 150.0,
        totalAmount: 150.0,
        varianceAmount: 0,
        hasQuantityVariance: false,
        hasPriceVariance: false,
        outstandingAmount: 150.0,
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
        userId: 2,
        amount: 100.0,
        paymentMethod: 'cash',
        status: 'pending_review',
      ),
    ];
  }

  int orderDetailCalls = 0;
  int supplierLedgerCalls = 0;
  int settingsCalls = 0;
  int updateSettingsCalls = 0;
  PurchasingSettings _settings = const PurchasingSettings(
    autoPoEnabled: false,
    autoPoLookbackDays: 30,
    autoPoMinStockTrigger: 0,
  );

  @override
  Future<PurchasingSettings> settings() async {
    settingsCalls++;
    return _settings;
  }

  @override
  Future<PurchasingSettings> updateSettings(PurchasingSettings settings) async {
    updateSettingsCalls++;
    _settings = settings;
    return _settings;
  }

  @override
  Future<PurchaseOrderDetail> orderDetail(int purchaseOrderId) async {
    orderDetailCalls++;
    return PurchaseOrderDetail(
      id: purchaseOrderId,
      supplierId: 1,
      userId: 2,
      status: 'partially_received',
      totalEstimatedAmount: 150.0,
      createdAt: '2026-08-17T10:00:00',
      orderedAt: '2026-08-17T11:00:00',
      items: [
        PurchaseOrderItemDetail(
          id: 21,
          purchaseOrderId: purchaseOrderId,
          productId: 3,
          quantityOrdered: 10,
          quantityReceived: 6,
          unitCost: 15.0,
          quantityInvoiced: 6,
          billedTotal: 90.0,
        ),
      ],
      timeline: [
        PurchaseOrderTimelineEvent(event: 'created', at: '2026-08-17T10:00:00'),
        PurchaseOrderTimelineEvent(event: 'ordered', at: '2026-08-17T11:00:00'),
        PurchaseOrderTimelineEvent(
          event: 'received',
          at: '2026-08-17T12:00:00',
          note: '+6 units',
        ),
      ],
      totalReceivedAmount: 90.0,
      totalBilledAmount: 90.0,
      outstandingPayable: 90.0,
    );
  }

  @override
  Future<SupplierLedger> supplierLedger(int supplierId) async {
    supplierLedgerCalls++;
    return SupplierLedger(
      supplierId: supplierId,
      supplierName: 'Acme Supply',
      openPurchaseOrders: 1,
      openPoAmount: 150.0,
      pendingInvoiceCount: 1,
      pendingInvoiceAmount: 150.0,
      approvedInvoiceTotal: 240.0,
      approvedPaymentTotal: 100.0,
      outstandingPayable: 140.0,
      entries: [
        SupplierLedgerEntry(
          kind: 'purchase_order',
          id: 11,
          status: 'pending_review',
          amount: 150.0,
          date: '2026-08-17T10:00:00',
          reference: 'PO-11',
        ),
        SupplierLedgerEntry(
          kind: 'invoice',
          id: 31,
          status: 'pending_review',
          amount: 150.0,
          date: '2026-08-18T10:00:00',
          reference: 'INV-001',
        ),
        SupplierLedgerEntry(
          kind: 'payment',
          id: 41,
          status: 'approved',
          amount: 100.0,
          date: '2026-08-19T10:00:00',
          reference: 'TRX-1',
        ),
      ],
    );
  }

  @override
  Future<PurchaseOrder> submitOrder(
    int purchaseOrderId, {
    String? reviewNote,
  }) async {
    submitOrderCalls++;
    lastOrderNote = reviewNote;
    return const PurchaseOrder(
      id: 11,
      supplierId: 1,
      userId: 2,
      status: 'pending_review',
      totalEstimatedAmount: 150.0,
      items: [],
    );
  }

  @override
  Future<PurchaseOrder> markOrdered(
    int purchaseOrderId, {
    String? reviewNote,
  }) async {
    markOrderedCalls++;
    lastOrderNote = reviewNote;
    return const PurchaseOrder(
      id: 11,
      supplierId: 1,
      userId: 2,
      status: 'ordered',
      totalEstimatedAmount: 150.0,
      items: [],
    );
  }

  @override
  Future<PurchaseOrder> rejectOrder(
    int purchaseOrderId, {
    String? reviewNote,
  }) async {
    rejectOrderCalls++;
    lastOrderNote = reviewNote;
    return const PurchaseOrder(
      id: 11,
      supplierId: 1,
      userId: 2,
      status: 'rejected',
      totalEstimatedAmount: 150.0,
      items: [],
    );
  }

  @override
  Future<PurchaseInvoice> submitInvoice(
    int invoiceId, {
    String? reviewNote,
  }) async {
    submitInvoiceCalls++;
    lastInvoiceNote = reviewNote;
    return const PurchaseInvoice(
      id: 31,
      supplierId: 1,
      purchaseOrderId: 11,
      userId: 2,
      invoiceNumber: 'INV-001',
      status: 'pending_review',
      subtotalAmount: 150.0,
      totalAmount: 150.0,
      varianceAmount: 0,
      hasQuantityVariance: false,
      hasPriceVariance: false,
      items: [],
    );
  }

  @override
  Future<PurchaseInvoice> approveInvoice(
    int invoiceId, {
    String? reviewNote,
  }) async {
    approveInvoiceCalls++;
    lastInvoiceNote = reviewNote;
    return const PurchaseInvoice(
      id: 31,
      supplierId: 1,
      purchaseOrderId: 11,
      userId: 2,
      invoiceNumber: 'INV-001',
      status: 'approved',
      subtotalAmount: 150.0,
      totalAmount: 150.0,
      varianceAmount: 0,
      hasQuantityVariance: false,
      hasPriceVariance: false,
      items: [],
    );
  }

  @override
  Future<PurchaseInvoice> rejectInvoice(
    int invoiceId, {
    String? reviewNote,
  }) async {
    rejectInvoiceCalls++;
    lastInvoiceNote = reviewNote;
    return const PurchaseInvoice(
      id: 31,
      supplierId: 1,
      purchaseOrderId: 11,
      userId: 2,
      invoiceNumber: 'INV-001',
      status: 'rejected',
      subtotalAmount: 150.0,
      totalAmount: 150.0,
      varianceAmount: 0,
      hasQuantityVariance: false,
      hasPriceVariance: false,
      items: [],
    );
  }

  @override
  Future<SupplierPayment> submitPayment(
    int paymentId, {
    String? reviewNote,
  }) async {
    submitPaymentCalls++;
    lastPaymentNote = reviewNote;
    return const SupplierPayment(
      id: 41,
      supplierId: 1,
      invoiceId: 31,
      userId: 2,
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
      userId: 2,
      amount: 100.0,
      paymentMethod: 'cash',
      status: 'draft',
    );
  }

  @override
  Future<SupplierPayment> approvePayment(
    int paymentId, {
    String? reviewNote,
  }) async {
    approvePaymentCalls++;
    lastPaymentNote = reviewNote;
    return const SupplierPayment(
      id: 41,
      supplierId: 1,
      invoiceId: 31,
      userId: 2,
      amount: 100.0,
      paymentMethod: 'cash',
      status: 'approved',
    );
  }

  @override
  Future<SupplierPayment> rejectPayment(
    int paymentId, {
    String? reviewNote,
  }) async {
    rejectPaymentCalls++;
    lastPaymentNote = reviewNote;
    return const SupplierPayment(
      id: 41,
      supplierId: 1,
      invoiceId: 31,
      userId: 2,
      amount: 100.0,
      paymentMethod: 'cash',
      status: 'rejected',
    );
  }
}

ProviderContainer _container({int ownerId = 1, bool isSuperuser = false}) {
  final auth = _FakeAuth(ownerId: ownerId, isSuperuser: isSuperuser);
  return ProviderContainer(
    overrides: [
      localizationControllerProvider.overrideWith(_FixedLanguageLocalization.new),
      authControllerProvider.overrideWith(() => auth),
      purchasingRepositoryProvider.overrideWithValue(_FakePurchasing()),
    ],
  );
}

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

  testWidgets('purchase orders tab shows PO with status', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pump(tester, container);

    await tester.tap(find.text('Purchase orders'));
    await tester.pumpAndSettle();

    expect(find.text('PO #11 · pending_review'), findsOneWidget);
  });

  testWidgets('review dialog sends review note on order approve', (tester) async {
    final container = _container(ownerId: 1);
    addTearDown(container.dispose);
    final fake = container.read(purchasingRepositoryProvider) as _FakePurchasing;
    await _pump(tester, container);

    await tester.tap(find.text('Purchase orders'));
    await tester.pumpAndSettle();

    await tester.tap(find.textContaining('PO #11'));
    await tester.pumpAndSettle();
    expect(find.text('Approve'), findsOneWidget);
    expect(find.text('Reject'), findsOneWidget);

    await tester.tap(find.text('Approve'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), 'good supplier');
    await tester.tap(find.text('Approve').last);
    await tester.pumpAndSettle();

    expect(fake.markOrderedCalls, 1);
    expect(fake.lastOrderNote, 'good supplier');
  });

  testWidgets('approver cannot review their own order', (tester) async {
    final container = _container(ownerId: 2);
    addTearDown(container.dispose);
    final fake = container.read(purchasingRepositoryProvider) as _FakePurchasing;
    await _pump(tester, container);

    await tester.tap(find.text('Purchase orders'));
    await tester.pumpAndSettle();

    await tester.tap(find.textContaining('PO #11'));
    await tester.pumpAndSettle();

    expect(find.text('Approve'), findsNothing);
    expect(find.text('Reject'), findsNothing);
    expect(fake.markOrderedCalls, 0);
  });

  testWidgets('superuser can approve their own order', (tester) async {
    final container = _container(ownerId: 2, isSuperuser: true);
    addTearDown(container.dispose);
    final fake = container.read(purchasingRepositoryProvider) as _FakePurchasing;
    await _pump(tester, container);

    await tester.tap(find.text('Purchase orders'));
    await tester.pumpAndSettle();

    await tester.tap(find.textContaining('PO #11'));
    await tester.pumpAndSettle();

    expect(find.text('Approve'), findsOneWidget);
    await tester.tap(find.text('Approve'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Approve').last);
    await tester.pumpAndSettle();

    expect(fake.markOrderedCalls, 1);
  });

  testWidgets('invoices tab shows pending review invoice', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pump(tester, container);

    await tester.tap(find.text('Purchase invoices'));
    await tester.pumpAndSettle();

    expect(find.text('INV-001 · pending_review'), findsOneWidget);
  });

  testWidgets('review dialog sends review note on invoice approve', (tester) async {
    final container = _container(ownerId: 1);
    addTearDown(container.dispose);
    final fake = container.read(purchasingRepositoryProvider) as _FakePurchasing;
    await _pump(tester, container);

    await tester.tap(find.text('Purchase invoices'));
    await tester.pumpAndSettle();

    await tester.tap(find.textContaining('INV-001'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Approve'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), 'all good');
    await tester.tap(find.text('Approve').last);
    await tester.pumpAndSettle();

    expect(fake.approveInvoiceCalls, 1);
    expect(fake.lastInvoiceNote, 'all good');
  });

  testWidgets('approver cannot review their own invoice', (tester) async {
    final container = _container(ownerId: 2);
    addTearDown(container.dispose);
    await _pump(tester, container);

    await tester.tap(find.text('Purchase invoices'));
    await tester.pumpAndSettle();

    await tester.tap(find.textContaining('INV-001'));
    await tester.pumpAndSettle();

    expect(find.text('Approve'), findsNothing);
    expect(find.text('Reject'), findsNothing);
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

  testWidgets('review dialog sends review note on payment approve', (tester) async {
    final container = _container(ownerId: 1);
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
    await tester.enterText(find.byType(TextField), 'paid in full');
    await tester.tap(find.text('Approve').last);
    await tester.pumpAndSettle();

    expect(fake.approvePaymentCalls, 1);
    expect(fake.lastPaymentNote, 'paid in full');
    expect(fake.createPaymentCalls, 0);
  });

  testWidgets('approver cannot review their own payment', (tester) async {
    final container = _container(ownerId: 2);
    addTearDown(container.dispose);
    await _pump(tester, container);

    await tester.tap(find.text('Supplier payments'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('#41 · pending_review'));
    await tester.pumpAndSettle();

    expect(find.text('Approve'), findsNothing);
    expect(find.text('Reject'), findsNothing);
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

  testWidgets('order detail shows timeline and invoiced totals', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    final fake = container.read(purchasingRepositoryProvider) as _FakePurchasing;
    await _pump(tester, container);

    await tester.tap(find.text('Purchase orders'));
    await tester.pumpAndSettle();
    await tester.tap(find.textContaining('PO #11'));
    await tester.pumpAndSettle();

    expect(fake.orderDetailCalls, 1);
    expect(find.text('Timeline'), findsOneWidget);
    expect(find.textContaining('Invoiced: 6'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.textContaining('Outstanding payable'),
      100,
      scrollable: find.byType(Scrollable).last,
    );
    expect(find.textContaining('+6 units'), findsOneWidget);
    expect(find.textContaining('Received amount'), findsOneWidget);
    expect(find.textContaining('Outstanding payable'), findsOneWidget);
  });

  testWidgets('ledger tab opens supplier ledger with entries', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    final fake = container.read(purchasingRepositoryProvider) as _FakePurchasing;
    await _pump(tester, container);

    await tester.tap(find.text('Ledger'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Acme Supply'));
    await tester.pumpAndSettle();

    expect(fake.supplierLedgerCalls, 1);
    expect(find.textContaining('Open POs'), findsOneWidget);
    expect(find.textContaining('Outstanding payable'), findsOneWidget);
    expect(find.text('PO-11'), findsOneWidget);
    expect(find.text('INV-001'), findsOneWidget);
    expect(find.text('TRX-1'), findsOneWidget);
  });

  testWidgets('automation settings dialog loads and saves', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    final fake = container.read(purchasingRepositoryProvider) as _FakePurchasing;
    await _pump(tester, container);

    await tester.tap(find.byTooltip('Automation settings'));
    await tester.pumpAndSettle();

    expect(fake.settingsCalls, 1);
    expect(find.text('Auto-generate purchase orders'), findsOneWidget);

    await tester.tap(find.text('Auto-generate purchase orders'));
    await tester.enterText(find.byType(TextField).at(0), '14');
    await tester.enterText(find.byType(TextField).at(1), '25');
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    expect(fake.updateSettingsCalls, 1);
    expect(fake._settings.autoPoEnabled, isTrue);
    expect(fake._settings.autoPoLookbackDays, 14);
    expect(fake._settings.autoPoMinStockTrigger, 25);
    expect(find.text('Automation settings saved'), findsOneWidget);
  });

  testWidgets('automation settings cancel does not save', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    final fake = container.read(purchasingRepositoryProvider) as _FakePurchasing;
    await _pump(tester, container);

    await tester.tap(find.byTooltip('Automation settings'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Cancel'));
    await tester.pumpAndSettle();

    expect(fake.updateSettingsCalls, 0);
  });
}
