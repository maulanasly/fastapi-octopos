/// End-of-shift: reconcile the drawer and view the result.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/money.dart';
import '../../core/models.dart';
import 'drawer_controller.dart';

class ReconcileScreen extends ConsumerStatefulWidget {
  const ReconcileScreen({super.key});

  @override
  ConsumerState<ReconcileScreen> createState() => _ReconcileScreenState();
}

class _ReconcileScreenState extends ConsumerState<ReconcileScreen> {
  final _countedCash = TextEditingController();
  final _countedNonCash = TextEditingController();
  bool _submitting = false;
  String? _error;
  ShiftReconciliation? _result;

  @override
  void dispose() {
    _countedCash.dispose();
    _countedNonCash.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      final counted = (double.tryParse(_countedCash.text) ?? 0) * 100;
      final nonCash = double.tryParse(_countedNonCash.text);
      final result = await ref
          .read(drawerControllerProvider.notifier)
          .reconcile(
            countedCashCents: counted.round(),
            countedNonCashCents: nonCash == null
                ? null
                : (nonCash * 100).round(),
          );
      setState(() => _result = result);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final drawerState = ref.watch(drawerControllerProvider);
    final session = drawerState.session;

    if (_result != null) {
      return _resultView(context, _result!);
    }

    if (session == null) {
      return const Scaffold(
        body: Center(child: Text('No open drawer to reconcile.')),
      );
    }

    return Scaffold(
      appBar: AppBar(title: const Text('End shift')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 480),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  'Drawer #${session.id}',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 8),
                Text(
                  'Opened with ${formatCents(centsFromApi(session.startingCash))}',
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _countedCash,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Counted cash',
                    prefixText: r'$ ',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _countedNonCash,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Counted non-cash (optional)',
                    prefixText: r'$ ',
                    border: OutlineInputBorder(),
                  ),
                ),
                if (_error != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text(
                      _error!,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.error,
                      ),
                    ),
                  ),
                const SizedBox(height: 20),
                FilledButton(
                  onPressed: _submitting ? null : _submit,
                  child: _submitting
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Reconcile & close drawer'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _resultView(BuildContext context, ShiftReconciliation rec) {
    final variance = centsFromApi(rec.cashVariance);
    return Scaffold(
      appBar: AppBar(title: const Text('Shift reconciled')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 480),
          child: Card(
            margin: const EdgeInsets.all(16),
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    'Reconciliation #${rec.id}',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 12),
                  _row(
                    context,
                    'Cash sales',
                    formatCents(centsFromApi(rec.cashSalesTotal)),
                  ),
                  _row(
                    context,
                    'Non-cash sales',
                    formatCents(centsFromApi(rec.nonCashSalesTotal)),
                  ),
                  _row(
                    context,
                    'Refunds',
                    formatCents(centsFromApi(rec.refundsTotal)),
                  ),
                  _row(
                    context,
                    'Gross sales',
                    formatCents(centsFromApi(rec.grossSalesTotal)),
                  ),
                  _row(
                    context,
                    'Net sales',
                    formatCents(centsFromApi(rec.netSalesTotal)),
                  ),
                  const Divider(height: 20),
                  _row(
                    context,
                    'Expected cash',
                    formatCents(centsFromApi(rec.expectedCash)),
                  ),
                  _row(
                    context,
                    'Counted cash',
                    formatCents(centsFromApi(rec.countedCash)),
                  ),
                  _row(
                    context,
                    'Variance',
                    formatCents(variance),
                    highlight: variance != 0,
                  ),
                  _row(context, 'Orders', '${rec.completedOrderCount}'),
                  const SizedBox(height: 16),
                  FilledButton(
                    onPressed: () => Navigator.of(context).pop(),
                    child: const Text('Done'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _row(
    BuildContext context,
    String label,
    String value, {
    bool highlight = false,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        children: [
          Expanded(child: Text(label)),
          Text(
            value,
            style: TextStyle(
              fontWeight: highlight ? FontWeight.bold : FontWeight.w500,
              color: highlight ? Theme.of(context).colorScheme.error : null,
            ),
          ),
        ],
      ),
    );
  }
}
