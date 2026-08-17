import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/api_client.dart';
import 'package:octopos_client/core/api_repositories.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/core/token_store.dart';
import 'package:octopos_client/features/admin/admin_screen.dart';

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

class _FakeAudit extends AuditRepository {
  _FakeAudit() : super(ApiClient(store: TokenStore(), onSessionExpired: () {}));

  @override
  Future<List<AuditLogEntry>> logs({String? action, int? userId}) async => [
    AuditLogEntry(
      id: 1,
      userId: 2,
      action: 'refund.create',
      resourceType: 'refund',
      resourceId: 5,
      detailsJson: '{"order_id": 9}',
      ipAddress: '127.0.0.1',
      createdAt: '2026-08-16T10:00:00',
    ),
    AuditLogEntry(
      id: 2,
      userId: 2,
      action: 'drawer.reconcile',
      resourceType: 'drawer_session',
      resourceId: 3,
      createdAt: '2026-08-16T09:00:00',
    ),
  ];
}

class _FakeRbacAdmin extends RbacAdminRepository {
  _FakeRbacAdmin()
    : super(ApiClient(store: TokenStore(), onSessionExpired: () {}));

  List<RoleInfo> storedRoles = const [
    RoleInfo(
      id: 1,
      name: 'cashier',
      description: 'POS cashier role',
      isSystem: true,
      permissions: ['orders:manage'],
    ),
    RoleInfo(
      id: 2,
      name: 'floor-manager',
      description: 'Floor manager',
      isSystem: false,
      permissions: ['products:manage'],
    ),
  ];

  @override
  Future<List<PermissionInfo>> permissions() async => const [
    PermissionInfo(id: 1, code: 'orders:manage'),
    PermissionInfo(id: 2, code: 'products:manage'),
    PermissionInfo(id: 3, code: 'reports:view'),
  ];

  @override
  Future<List<RoleInfo>> roles() async => storedRoles;

  @override
  Future<List<UserProfile>> users() async => const [
    UserProfile(
      id: 1,
      email: 'cashier@example.com',
      fullName: 'Budi',
      isActive: true,
      isSuperuser: false,
    ),
  ];

  int creates = 0;

  @override
  Future<RoleInfo> createRole(
    String name,
    String? description,
    List<String> permissionCodes,
  ) async {
    creates++;
    final role = RoleInfo(
      id: 99,
      name: name,
      description: description,
      isSystem: false,
      permissions: permissionCodes,
    );
    storedRoles = [...storedRoles, role];
    return role;
  }
}

ProviderContainer _container() => ProviderContainer(
  overrides: [
    localizationControllerProvider.overrideWith(_FixedLanguageLocalization.new),
    auditRepositoryProvider.overrideWithValue(_FakeAudit()),
    rbacAdminRepositoryProvider.overrideWithValue(_FakeRbacAdmin()),
  ],
);

Future<void> _pump(WidgetTester tester, ProviderContainer container) async {
  await tester.pumpWidget(
    UncontrolledProviderScope(
      container: container,
      child: const MaterialApp(home: AdminScreen()),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('audit tab lists entries with filters', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pump(tester, container);

    expect(find.text('refund.create · user 2'), findsOneWidget);
    expect(find.textContaining('refund#5'), findsOneWidget);
    expect(find.text('drawer.reconcile · user 2'), findsOneWidget);
  });

  testWidgets('audit detail dialog shows the JSON payload', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pump(tester, container);

    await tester.tap(find.byIcon(Icons.chevron_right).first);
    await tester.pumpAndSettle();

    expect(find.text('{"order_id": 9}'), findsOneWidget);
  });

  testWidgets('roles tab lists and creates a role', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pump(tester, container);

    await tester.tap(find.text('Roles'));
    await tester.pumpAndSettle();

    expect(find.text('cashier (System)'), findsOneWidget);
    expect(find.text('floor-manager'), findsOneWidget);

    await tester.tap(find.byIcon(Icons.add));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.widgetWithText(TextField, 'Role name'),
      'floor-lead',
    );
    await tester.tap(find.text('orders:manage'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    final fake = container.read(rbacAdminRepositoryProvider) as _FakeRbacAdmin;
    expect(fake.creates, 1);
    expect(find.text('floor-lead'), findsOneWidget);
  });
}
