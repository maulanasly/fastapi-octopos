/// Outbox repository: failed rows are readable, re-queueable, and
/// removable; stored error codes survive the round trip.
library;

import 'package:drift/native.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/db/app_database.dart';
import 'package:octopos_client/core/db/database_provider.dart';
import 'package:octopos_client/core/sync/outbox_repository.dart';
ProviderContainer _container(AppDatabase db) => ProviderContainer(
  overrides: [appDatabaseProvider.overrideWithValue(db)],
);

Future<int> _enqueue(OutboxRepository repo) => repo.enqueueOrder(
  items: const [
    {'product_id': 1, 'quantity': 2},
  ],
);

void main() {
  test('failed rows round-trip through retry back to pending', () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final container = _container(db);
    addTearDown(container.dispose);
    final repo = container.read(outboxRepositoryProvider);

    final id = await _enqueue(repo);
    expect(await repo.pendingOrders(), hasLength(1));
    expect(await repo.failedOrders(), isEmpty);

    await repo.markFailed(id, 'http_422');
    expect(await repo.pendingOrders(), isEmpty);
    final failed = await repo.failedOrders();
    expect(failed, hasLength(1));
    expect(failed.first.id, id);
    expect(failed.first.lastError, 'http_422');

    await repo.retry(id);
    final pending = await repo.pendingOrders();
    expect(pending, hasLength(1));
    expect(pending.first.lastError, isNull);
    expect(await repo.failedOrders(), isEmpty);
  });

  test('remove discards a failed row', () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final container = _container(db);
    addTearDown(container.dispose);
    final repo = container.read(outboxRepositoryProvider);

    final id = await _enqueue(repo);
    await repo.markFailed(id, 'unexpected_error');
    await repo.remove(id);

    expect(await repo.failedOrders(), isEmpty);
    expect(await repo.pendingOrders(), isEmpty);
  });

  test('watchFailed emits on failure and retry', () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final container = _container(db);
    addTearDown(container.dispose);
    final repo = container.read(outboxRepositoryProvider);

    final id = await _enqueue(repo);
    await repo.markFailed(id, 'http_422');
    // A fresh subscription emits the current state first.
    await expectLater(repo.watchFailed().map((r) => r.length), emits(1));

    await repo.retry(id);
    await expectLater(repo.watchFailed().map((r) => r.length), emits(0));
  });
}
