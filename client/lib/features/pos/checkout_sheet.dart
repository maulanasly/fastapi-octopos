/// Checkout sheet: promotion code, loyalty points, payment method,
/// quick-cash chips, and split payments.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';

import '../../core/api_repositories.dart';
import '../../core/errors.dart';
import '../../core/money.dart';
import '../../core/strings.dart';
import 'cart_controller.dart';

enum _PayMethod { cash, card, split }

class CheckoutSheet extends ConsumerStatefulWidget {
  const CheckoutSheet({super.key});

  @override
  ConsumerState<CheckoutSheet> createState() => _CheckoutSheetState();
}

class _CheckoutSheetState extends ConsumerState<CheckoutSheet> {
  final _promo = TextEditingController();
  final _destination = TextEditingController();
  _PayMethod _method = _PayMethod.cash;
  final _cashReceived = TextEditingController();
  final _splitCash = TextEditingController();
  int _redeemPoints = 0;
  bool _submitting = false;
  bool _locating = false;
  double? _pinLat;
  double? _pinLng;
  String? _error;

  /// Stable per-sheet idempotency keys: reused across retries so a
  /// network timeout after the server accepted the request never
  /// duplicates the order or payment on a second tap of Pay.
  String? _orderKey;
  String? _payKey;

  String get _orderKeyOnce => _orderKey ??= newIdempotencyKey();
  String get _payKeyOnce => _payKey ??= newIdempotencyKey();

  @override
  void dispose() {
    _promo.dispose();
    _destination.dispose();
    _cashReceived.dispose();
    _splitCash.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    final cart = ref.watch(cartControllerProvider);
    final total = cart.subtotalCents;
    final customer = cart.customer;
    final maxRedeemable = customer == null
        ? 0
        : customer.pointsBalance.clamp(0, total);

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
              '${s.of('checkout')} — ${formatCents(total)}',
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
            if (customer != null && customer.pointsBalance > 0) ...[
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: Text(
                      '${s.of('pointsBalance')}: ${customer.pointsBalance}',
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ),
                  IconButton(
                    tooltip: s.of('redeemPoints'),
                    icon: const Icon(Icons.stars),
                    onPressed: () {
                      setState(() {
                        _redeemPoints = maxRedeemable;
                      });
                    },
                  ),
                ],
              ),
              if (_redeemPoints > 0)
                Slider(
                  value: _redeemPoints.toDouble(),
                  max: maxRedeemable.toDouble().clamp(1, double.infinity),
                  label: '${s.of('redeemPoints')}: $_redeemPoints',
                  onChanged: (v) => setState(() => _redeemPoints = v.round()),
                ),
            ],
            const SizedBox(height: 12),
            TextField(
              controller: _destination,
              decoration: InputDecoration(
                labelText: s.of('serviceAddress'),
                hintText: s.of('destination'),
                border: const OutlineInputBorder(),
                isDense: true,
              ),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _locating ? null : _setPin,
                    icon: _locating
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.my_location),
                    label: Text(s.of('useMyLocation')),
                  ),
                ),
                if (_pinLat != null && _pinLng != null) ...[
                  const SizedBox(width: 8),
                  Flexible(
                    child: Text(
                      '${_pinLat!.toStringAsFixed(5)}, '
                      '${_pinLng!.toStringAsFixed(5)}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ),
                ],
              ],
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
                ButtonSegment(
                  value: _PayMethod.split,
                  label: Text(s.of('split')),
                  icon: const Icon(Icons.call_split),
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
                  errorText: _cashError(total),
                ),
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                children: [
                  for (final amount in _quickCashAmounts(total))
                    ActionChip(
                      label: Text(formatCents(amount)),
                      onPressed: () => setState(() {
                        _cashReceived.text = centsToApi(amount);
                      }),
                    ),
                ],
              ),
            ],
            if (_method == _PayMethod.split) ...[
              const SizedBox(height: 12),
              TextField(
                controller: _splitCash,
                keyboardType: TextInputType.number,
                decoration: InputDecoration(
                  labelText: s.of('splitCash'),
                  prefixText: r'$ ',
                  border: const OutlineInputBorder(),
                  isDense: true,
                ),
              ),
              Text(
                s.of(
                  'splitHint',
                  args: {
                    'card': formatCents((total - _splitCents).clamp(0, total)),
                  },
                ),
                style: Theme.of(context).textTheme.bodySmall,
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

  int get _splitCents => centsFromInput(_splitCash.text);

  /// Captures the device position as the service pin (optional).
  Future<void> _setPin() async {
    setState(() => _locating = true);
    try {
      final position = await Geolocator.getCurrentPosition();
      setState(() {
        _pinLat = position.latitude;
        _pinLng = position.longitude;
      });
    } catch (_) {
      if (mounted) {
        final strings = ref.read(stringsProvider);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(strings.of('locationUnavailable'))),
        );
      }
    } finally {
      if (mounted) setState(() => _locating = false);
    }
  }

  /// Cash-chip presets: exact amount, then common banknotes in cents.
  List<int> _quickCashAmounts(int total) {
    final notes = currentCurrency == 'IDR'
        ? const [10000000, 5000000, 2000000, 1000000, 500000, 100000, 50000]
        : const [10000, 5000, 2000, 1000, 500, 100];
    final presets = <int>[total];
    for (final note in notes) {
      if (note >= total && !presets.contains(note)) presets.add(note);
    }
    return presets;
  }

  String? _cashError(int total) {
    final s = ref.read(stringsProvider);
    final received = centsFromInput(_cashReceived.text);
    if (received <= 0) return null;
    if (received < total) return s.of('insufficientCash');
    return null;
  }

  Future<void> _submit(BuildContext context) async {
    final strings = ref.read(stringsProvider);
    final cart = ref.read(cartControllerProvider);
    final promo = _promo.text.trim();
    final total = cart.subtotalCents;
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
        redeemPoints: _redeemPoints,
        destinationAddress: _destination.text.trim().isEmpty
            ? null
            : _destination.text.trim(),
        destinationLat: _pinLat,
        destinationLng: _pinLng,
        idempotencyKey: _orderKeyOnce,
      );

      // 2. Settle it (single or split). The payments endpoint returns the
      // created PaymentLine; the order itself is what the receipt needs.
      if (_method == _PayMethod.split) {
        final cash = _splitCents.clamp(0, total);
        final card = total - cash;
        if (cash > 0 && card > 0) {
          await orders.addSplitPayments(
            orderId: order.id,
            payments: [
              {'payment_method': 'cash', 'amount': centsToApi(cash)},
              {'payment_method': 'card', 'amount': centsToApi(card)},
            ],
          );
        } else if (cash > 0) {
          await orders.addPayment(
            orderId: order.id,
            method: 'cash',
            amountCents: cash,
            idempotencyKey: _payKeyOnce,
          );
        } else {
          await orders.addPayment(
            orderId: order.id,
            method: 'card',
            amountCents: card,
            idempotencyKey: _payKeyOnce,
          );
        }
      } else if (_method == _PayMethod.cash) {
        final received = centsFromInput(_cashReceived.text);
        await orders.addPayment(
          orderId: order.id,
          method: 'cash',
          amountCents: received > 0 ? received : total,
          idempotencyKey: _payKeyOnce,
        );
      } else {
        await orders.addPayment(
          orderId: order.id,
          method: 'card',
          amountCents: total,
          idempotencyKey: _payKeyOnce,
        );
      }
      if (mounted && context.mounted) Navigator.of(context).pop(order);
    } catch (e) {
      if (mounted) setState(() => _error = friendlyError(e, strings));
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }
}
