/// Order receipt screen (fetched fresh from the backend).
library;

import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api_repositories.dart';
import '../../core/async_views.dart';
import '../../core/dates.dart';
import '../../core/errors.dart';
import '../../core/layout.dart';
import '../../core/strings.dart';
import '../../core/money.dart';
import '../../core/models.dart';
import 'print_stub.dart' if (dart.library.js_interop) 'print_web.dart';

class ReceiptScreen extends ConsumerStatefulWidget {
  const ReceiptScreen({super.key, required this.orderId});

  final int orderId;

  @override
  ConsumerState<ReceiptScreen> createState() => _ReceiptScreenState();
}

class _ReceiptScreenState extends ConsumerState<ReceiptScreen> {
  late Future<OrderReceipt> _future;

  @override
  void initState() {
    super.initState();
    _future = ref.read(orderRepositoryProvider).receipt(widget.orderId);
  }

  /// Closes the receipt. Pushed flows pop back to their opener;
  /// a cold-started deep link has nothing to pop, so it lands on POS
  /// (open to every signed-in role) instead of stranding the user.
  void _close(BuildContext context) {
    if (context.canPop()) {
      context.pop();
    } else {
      context.go('/pos');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: BackButton(onPressed: () => _close(context)),
        title: Text(
          ref.read(stringsProvider).of('orderId', args: {'id': widget.orderId}),
        ),
      ),
      body: FutureBuilder<OrderReceipt>(
        future: _future,
        builder: (context, snapshot) {
          final s = ref.watch(stringsProvider);
          if (snapshot.connectionState != ConnectionState.done) {
            return const LoadingStateView();
          }
          if (snapshot.hasError) {
            return ErrorStateView(
              message: friendlyError(snapshot.error!, s),
              onRetry: () => setState(
                () => _future = ref.read(orderRepositoryProvider).receipt(widget.orderId),
              ),
            );
          }
          final receipt = snapshot.data!;
          return Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: AppBreakpoints.dialogMax),
              child: Card(
                margin: const EdgeInsets.all(AppSpacing.lg),
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.xl),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        'OctoPOS',
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      Text(
                        '${s.of('orderId', args: {'id': receipt.orderId})} — ${_statusLabel(s, receipt.status)}',
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                      Text(
                        '${s.of('date')}: ${formatDateTimeIso(receipt.createdAt)}',
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                      Text(
                        '${s.of('cashier')}: ${receipt.cashierName ?? '-'}',
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                      Text(
                        receipt.customerName ?? s.of('guest'),
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                      const Divider(height: 24),
                      for (final item in receipt.items)
                        Padding(
                          padding: const EdgeInsets.symmetric(vertical: 2),
                          child: Row(
                            children: [
                              Expanded(
                                child: Text(
                                  '${item.quantity} × ${formatCents(centsFromApi(item.unitPrice))}',
                                ),
                              ),
                              Text(formatCents(centsFromApi(item.lineTotal))),
                            ],
                          ),
                        ),
                      const Divider(height: 24),
                      _line(context, s.of('subtotal'), receipt.subtotalAmount),
                      if (receipt.discountAmount > 0)
                        _line(
                          context,
                          s.of('discount'),
                          -receipt.discountAmount,
                        ),
                      if (receipt.taxTotalAmount > 0)
                        _line(context, s.of('tax'), receipt.taxTotalAmount),
                      _line(
                        context,
                        s.of('total'),
                        receipt.grandTotalAmount,
                        bold: true,
                      ),
                      const SizedBox(height: AppSpacing.sm),
                      for (final payment in receipt.payments)
                        _line(
                          context,
                          s.of(
                            'paid',
                            args: {'method': payment.paymentMethod},
                          ),
                          payment.amount,
                        ),
                      if (receipt.changeAmount > 0)
                        _line(context, s.of('change'), -receipt.changeAmount),
                      const SizedBox(height: AppSpacing.lg),
                      if (kIsWeb)
                        FilledButton.icon(
                          icon: const Icon(Icons.print),
                          label: Text(s.of('print')),
                          onPressed: printReceipt,
                        ),
                      const SizedBox(height: AppSpacing.sm),
                      FilledButton.icon(
                        icon: const Icon(Icons.check),
                        label: Text(s.of('done')),
                        onPressed: () => _close(context),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  String _statusLabel(AppStrings s, String status) => switch (status) {
    'serving' => s.of('statusServing'),
    'completed' => s.of('statusCompleted'),
    'cancelled' => s.of('statusCancelled'),
    _ => s.of('statusPending'),
  };

  Widget _line(
    BuildContext context,
    String label,
    double amount, {
    bool bold = false,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        children: [
          Expanded(
            child: Text(
              label,
              style: bold ? const TextStyle(fontWeight: FontWeight.bold) : null,
            ),
          ),
          Text(
            formatCents(centsFromApi(amount)),
            style: bold
                ? const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)
                : null,
          ),
        ],
      ),
    );
  }
}
