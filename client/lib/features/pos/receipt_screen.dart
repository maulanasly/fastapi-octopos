/// Order receipt screen (fetched fresh from the backend).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/money.dart';
import '../../core/models.dart';

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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Receipt #${widget.orderId}')),
      body: FutureBuilder<OrderReceipt>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(
              child: Text('Failed to load receipt:\n${snapshot.error}'),
            );
          }
          final receipt = snapshot.data!;
          return Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Card(
                margin: const EdgeInsets.all(16),
                child: Padding(
                  padding: const EdgeInsets.all(24),
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
                        'Order #${receipt.orderId} — ${receipt.status}',
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
                      _line(context, 'Subtotal', receipt.subtotalAmount),
                      if (receipt.discountAmount > 0)
                        _line(context, 'Discount', -receipt.discountAmount),
                      if (receipt.taxTotalAmount > 0)
                        _line(context, 'Tax', receipt.taxTotalAmount),
                      _line(
                        context,
                        'Total',
                        receipt.grandTotalAmount,
                        bold: true,
                      ),
                      const SizedBox(height: 8),
                      for (final payment in receipt.payments)
                        _line(
                          context,
                          'Paid (${payment.paymentMethod})',
                          payment.amount,
                        ),
                      if (receipt.changeAmount > 0)
                        _line(context, 'Change', -receipt.changeAmount),
                      const SizedBox(height: 16),
                      FilledButton.icon(
                        icon: const Icon(Icons.check),
                        label: const Text('Done'),
                        onPressed: () => Navigator.of(context).pop(),
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
