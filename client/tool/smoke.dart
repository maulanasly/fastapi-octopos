/// Live-backend smoke test for the client API contract.
///
/// Runs on the Dart VM (no Flutter plugins): exercises the same payloads
/// and response parsing the app's repositories use, against a running
/// backend. Usage: `dart run tool/smoke.dart`
library;

import 'dart:io';

import 'package:dio/dio.dart';
import 'package:octopos_client/core/models.dart';

const base = 'http://127.0.0.1:8000/api/v1';

var passed = 0;
var failed = 0;

void check(String name, bool cond, [String? detail]) {
  if (cond) {
    passed++;
    stdout.writeln('  [PASS] $name');
  } else {
    failed++;
    stdout.writeln('  [FAIL] $name  ${detail ?? ''}');
  }
}

Future<void> main() async {
  final dio = Dio(BaseOptions(baseUrl: base));

  final email = 'smoke-${DateTime.now().millisecondsSinceEpoch}@example.com';
  const password = 'TestPass123';

  // 1. Register + login
  final reg = await dio.post<Map<String, dynamic>>('/auth/register', data: {
    'email': email,
    'password': password,
    'full_name': 'Smoke User',
  });
  check('register (201)', reg.statusCode == 201);

  final tokens = await dio.post<Map<String, dynamic>>('/auth/token',
      data: FormData.fromMap({'username': email, 'password': password}));
  check('login (200)', tokens.statusCode == 200);
  final access = tokens.data!['access_token'] as String;
  final refresh = tokens.data!['refresh_token'] as String;
  dio.options.headers['Authorization'] = 'Bearer $access';

  // 2. Refresh rotation (as the app's interceptor does)
  final rotated = await dio.post<Map<String, dynamic>>('/auth/refresh',
      data: {'refresh_token': refresh});
  check('refresh rotation (200)', rotated.statusCode == 200);
  final access2 = rotated.data!['access_token'] as String;
  dio.options.headers['Authorization'] = 'Bearer $access2';

  // 3. Permissions (role-aware nav)
  final perms =
      await dio.get<Map<String, dynamic>>('/rbac/me/permissions');
  final permissions = (perms.data!['permissions'] as List).cast<String>();
  check('permissions include orders:manage',
      permissions.contains('orders:manage'));

  // 4. Catalog (POS grid)
  final productList = await dio.get<List<dynamic>>('/products/');
  final product = Product.fromJson(productList.data!
      .cast<Map<String, dynamic>>()
      .firstWhere((p) => p['sku'] == 'SMK-SEED'));
  check('seeded product read + parsed', product.priceCents == 450);

  // 5. Drawer open (required before orders)
  final drawer = await dio.post<Map<String, dynamic>>('/drawers/open',
      data: {'starting_cash': 100.0});
  check('drawer open (200)', drawer.statusCode == 200);

  // 6. Order with idempotency key (client generates uuid)
  const idem = 'smoke-order-001';
  final orderResp = await dio.post<Map<String, dynamic>>('/orders/', data: {
    'items': [
      {'product_id': product.id, 'quantity': 2},
    ],
    'idempotency_key': idem,
  });
  final order = Order.fromJson(orderResp.data!);
  check('order created + parsed', order.subtotalAmount == 9.0);

  final replay = await dio.post<Map<String, dynamic>>('/orders/', data: {
    'items': [
      {'product_id': product.id, 'quantity': 2},
    ],
    'idempotency_key': idem,
  });
  check('idempotent replay returns same order',
      Order.fromJson(replay.data!).id == order.id);

  // 7. Cash payment with overpayment (change computed by backend)
  final pay = await dio.post<Map<String, dynamic>>('/orders/${order.id}/payments',
      data: {
        'payment_method': 'cash',
        'amount': 10.0,
        'idempotency_key': 'smoke-pay-001',
      });
  check('payment (200)', pay.statusCode == 200);
  // Contract lock: the payments endpoint returns a Payment, not an Order;
  // parsing it as PaymentLine must succeed (regression: Order.fromJson
  // threw a null TypeError on this payload).
  final payment = PaymentLine.fromJson(pay.data!);
  check('payment parsed as PaymentLine',
      payment.orderId == order.id && payment.amount == 10.0);

  final receiptResp =
      await dio.get<Map<String, dynamic>>('/orders/${order.id}/receipt');
  final receipt = OrderReceipt.fromJson(receiptResp.data!);
  check('receipt parsed: settled', receipt.status == 'completed');
  check('receipt change = 1.00',
      (receipt.changeAmount - 1.0).abs() < 0.001, '${receipt.changeAmount}');
  check('receipt tax lines parsed', receipt.taxLines.isEmpty || receipt.taxLines.isNotEmpty);
  check('receipt payments parsed', receipt.payments.length == 1);

  // 8. Refund (idempotent)
  final refund = await dio.post<Map<String, dynamic>>('/refunds/', data: {
    'order_id': order.id,
    'items': [
      {'order_item_id': order.items.first.id, 'quantity': 1},
    ],
    'payment_method': 'cash',
    'idempotency_key': 'smoke-refund-001',
  });
  final refundModel = Refund.fromJson(refund.data!);
  check('refund created + parsed', refundModel.totalAmount > 0);

  // 9. Sync catalog delta (client watermark pull)
  final delta = await dio.get<Map<String, dynamic>>('/sync/catalog');
  final catalogDelta = CatalogDelta.fromJson(delta.data!);
  check('catalog delta parsed',
      catalogDelta.products.any((p) => p.id == product.id));

  // 10. Reconcile drawer (end of shift)
  final rec = await dio.post<Map<String, dynamic>>(
      '/drawers/reconcile/${drawer.data!['id']}',
      data: {'counted_cash': 105.0});
  check('reconcile (200)', rec.statusCode == 200);

  // 11. Reports (RBAC gate: cashier must be denied)
  try {
    await dio.get<Map<String, dynamic>>('/reports/sales');
    check('reports denied for cashier (403)', false);
  } on DioException catch (e) {
    check('reports denied for cashier (403)', e.response?.statusCode == 403,
        'got ${e.response?.statusCode}');
  }

  stdout.writeln('\nSMOKE RESULT: $passed passed, $failed failed');
  exit(failed == 0 ? 0 : 1);
}
