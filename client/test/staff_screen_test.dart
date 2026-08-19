import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/api_client.dart';
import 'package:octopos_client/core/api_repositories.dart';
import 'package:octopos_client/core/auth_controller.dart';
import 'package:octopos_client/core/localization_controller.dart';
import 'package:octopos_client/core/models.dart';
import 'package:octopos_client/core/token_store.dart';
import 'package:octopos_client/features/staff/staff_screen.dart';

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
    email: 'owner@example.com',
    fullName: 'Owner',
    permissions: {'users:manage', 'users:manage_roles'},
    isSuperuser: false,
  );
}

class _FakeStaff extends StaffRepository {
  _FakeStaff()
    : super(ApiClient(store: TokenStore(), onSessionExpired: () {}));

  final staff = <UserProfile>[
    const UserProfile(
      id: 2,
      email: 'cashier@example.com',
      fullName: 'Cashier',
      isActive: true,
      isSuperuser: false,
      tenantId: 1,
      roles: ['cashier'],
    ),
    const UserProfile(
      id: 3,
      email: 'old@example.com',
      fullName: 'Former',
      isActive: false,
      isSuperuser: false,
      tenantId: 1,
      roles: ['cashier'],
    ),
  ];

  bool created = false;

  @override
  Future<List<UserProfile>> users() async => List.of(staff);

  @override
  Future<UserProfile> createUser({
    required String email,
    String? fullName,
    required String password,
  }) async {
    created = true;
    return UserProfile(
      id: 99,
      email: email,
      fullName: fullName,
      isActive: true,
      isSuperuser: false,
      tenantId: 1,
      roles: const ['cashier'],
    );
  }
}

class _FakeRbacAdmin extends RbacAdminRepository {
  _FakeRbacAdmin()
    : super(ApiClient(store: TokenStore(), onSessionExpired: () {}));

  @override
  Future<List<RoleInfo>> roles() async => const [
    RoleInfo(id: 1, name: 'cashier', isSystem: true),
    RoleInfo(id: 2, name: 'manager', isSystem: true),
  ];

  @override
  Future<List<PermissionInfo>> permissions() async => const [];

  @override
  Future<void> assignRoles(int userId, List<int> roleIds) async {}
}

ProviderContainer _container() => ProviderContainer(
  overrides: [
    localizationControllerProvider.overrideWith(_FixedLanguageLocalization.new),
    authControllerProvider.overrideWith(_FakeAuth.new),
    staffRepositoryProvider.overrideWithValue(_FakeStaff()),
    rbacAdminRepositoryProvider.overrideWithValue(_FakeRbacAdmin()),
  ],
);

Future<void> _pump(WidgetTester tester, ProviderContainer container) async {
  await tester.pumpWidget(
    UncontrolledProviderScope(
      container: container,
      child: const MaterialApp(home: StaffScreen()),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('lists staff with roles and active state', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pump(tester, container);

    expect(find.text('Cashier'), findsOneWidget);
    expect(find.textContaining('cashier@example.com'), findsOneWidget);
    expect(find.textContaining('cashier'), findsWidgets);
    expect(find.text('Former'), findsOneWidget);
    // Inactive staff show no deactivate button; the current user is excluded too.
    expect(find.byIcon(Icons.person_off_outlined), findsOneWidget);
  });

  testWidgets('create staff dialog posts a new user', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    final fake = container.read(staffRepositoryProvider) as _FakeStaff;
    await _pump(tester, container);

    await tester.tap(find.byType(FloatingActionButton));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.widgetWithText(TextField, 'Email'),
      'newbie@example.com',
    );
    await tester.enterText(
      find.widgetWithText(TextField, 'Full name'),
      'Newbie',
    );
    await tester.enterText(
      find.widgetWithText(TextField, 'Password'),
      'Secret123',
    );
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    expect(fake.created, isTrue);
    expect(find.textContaining('newbie@example.com'), findsOneWidget);
  });

  testWidgets('role assignment dialog shows system roles', (tester) async {
    final container = _container();
    addTearDown(container.dispose);
    await _pump(tester, container);

    await tester.tap(find.byIcon(Icons.group_add_outlined).first);
    await tester.pumpAndSettle();

    expect(find.text('Assign roles'), findsOneWidget);
    expect(find.text('cashier'), findsWidgets);
    expect(find.text('manager'), findsOneWidget);
  });
}
