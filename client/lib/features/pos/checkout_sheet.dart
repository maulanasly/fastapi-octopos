/// Checkout sheet: promotion code, payment method, and settlement.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/strings.dart';
import '../../core/money.dart';
import 'cart_controller.dart';

enum _PayMethod { cash, card }

class CheckoutSheet extends ConsumerStatefulWidget {
  const CheckoutSheet({super.key});

  @override
  ConsumerState<CheckoutSheet> createState() => _CheckoutSheetState();
}

class _CheckoutSheetState extends ConsumerState<CheckoutSheet> {
  final _promo = TextEditingController();
  _PayMethod _method = _PayMethod.cash;
  final _cashReceived = TextEditingController();
  bool _submitting = false;
  String? _error;

  @override
  void dispose() {
    _promo.dispose();
    _cashReceived.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    final cart = ref.watch(cartControllerProvider);
    final subtotal = cart.subtotalCents;

    return Padding(
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'Checkout — ${formatCents(subtotal)}',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _promo,
              decoration: InputDecoration(
                labelText: s.of('promotionCode'),
                border: const OutlineInputBorder(),
                isDense: true,
              ),
            ),
            const SizedBox(height: 12),
            SegmentedButton<_PayMethod>(
              segments: [
                ButtonSegment(
                  value: _PayMethod.cash,
                  label: Text(s.of('cash')),
                  icon: const Icon(Icons.payments),
                ),
                ButtonSegment(
                  value: _PayMethod.card,
                  label: Text(s.of('card')),
                  icon: const Icon(Icons.credit_card),
                ),
              ],
              selected: {_method},
              onSelectionChanged: (s) => setState(() => _method = s.first),
            ),
            if (_method == _PayMethod.cash) ...[
              const SizedBox(height: 12),
              TextField(
                controller: _cashReceived,
                keyboardType: TextInputType.number,
                decoration: InputDecoration(
                  labelText: s.of('cashReceived'),
                  prefixText: r'$ ',
                  border: const OutlineInputBorder(),
                  isDense: true,
                  errorText: _cashError(subtotal),
                ),
              ),
            ],
            if (_error != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(
                  _error!,
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
              ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: _submitting ? null : () => _submit(context),
              child: _submitting
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Text(s.of('pay')),
            ),
          ],
        ),
      ),
    );
  }

  String? _cashError(int subtotal) {
    final s = ref.read(stringsProvider);
    final received = (double.tryParse(_cashReceived.text) ?? 0) * 100;
    if (received <= 0) return null;
    if (received < subtotal) return s.of('insufficientCash');
    return null;
  }

  Future<void> _submit(BuildContext context) async {
    final cart = ref.read(cartControllerProvider);
    final promo = _promo.text.trim();
    setState(() {
      _submitting = true;
      _error = null;
    });

    try {
      final orders = ref.read(orderRepositoryProvider);

      // 1. Create the order (idempotent).
      final order = await orders.createOrder(
        items: [
          for (final line in cart.lines.values)
            {'product_id': line.product.id, 'quantity': line.quantity},
        ],
        customerId: cart.customer?.id,
        promotionCode: promo.isEmpty ? null : promo,
      );

      // 2. Settle it (single or split). The payments endpoint returns the
      // created PaymentLine; the order itself is what the receipt needs.
      if (_method == _PayMethod.cash) {
        final received =
            (double.tryParse(_cashReceived.text) ?? 0).round() * 100;
        await orders.addPayment(
          orderId: order.id,
          method: 'cash',
          amountCents: received > 0 ? received : cart.subtotalCents,
        );
      } else {
        await orders.addPayment(
          orderId: order.id,
          method: 'card',
          amountCents: cart.subtotalCents,
        );
      }
      if (mounted && context.mounted) Navigator.of(context).pop(order);
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }
}
