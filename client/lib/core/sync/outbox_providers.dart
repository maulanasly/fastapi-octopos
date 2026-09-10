/// Shared outbox streams: pending queue depth for the POS banner and
/// the failed queue for the review dialog. Both delegate to the
/// repository (drift) so screens never query tables inline.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../db/app_database.dart';
import 'outbox_repository.dart';

final pendingOutboxProvider = StreamProvider<List<OutboxOrder>>((ref) {
  return ref.watch(outboxRepositoryProvider).watchPending();
});

final failedOutboxProvider = StreamProvider<List<OutboxOrder>>((ref) {
  return ref.watch(outboxRepositoryProvider).watchFailed();
});
