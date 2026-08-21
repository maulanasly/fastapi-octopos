/// Purchasing hub: suppliers, purchase orders (create → ordered → receive),
/// and purchase invoices (create → review → approve/reject).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/async_views.dart';
import '../../core/auth_controller.dart';
import '../../core/dates.dart';
import '../../core/errors.dart';
import '../../core/layout.dart';
import '../../core/models.dart';
import '../../core/strings.dart';
import '../../core/money.dart';
import '../pos/catalog_controller.dart';

class PurchasingScreen extends ConsumerStatefulWidget {
  const PurchasingScreen({super.key});

  @override
  ConsumerState<PurchasingScreen> createState() => _PurchasingScreenState();
}

class _PurchasingScreenState extends ConsumerState<PurchasingScreen> {
  int _tab = 0;
  late Future<List<Supplier>> _suppliers;
  late Future<List<PurchaseOrder>> _orders;
  late Future<List<PurchaseInvoice>> _invoices;
  late Future<List<SupplierPayment>> _payments;
  String? _orderStatus;
  String? _invoiceStatus;
  String? _paymentStatus;

  @override
  void initState() {
    super.initState();
    _reload();
  }

  void _reload() {
    _suppliers = ref.read(purchasingRepositoryProvider).suppliers();
    _orders = ref
        .read(purchasingRepositoryProvider)
        .orders(status: _orderStatus);
    _invoices = ref
        .read(purchasingRepositoryProvider)
        .invoices(status: _invoiceStatus);
    _payments = ref
        .read(purchasingRepositoryProvider)
        .payments(status: _paymentStatus);
  }

  Future<void> _refresh() async {
    _reload();
    await Future.wait<void>([_orders, _invoices, _payments]);
  }

  Future<void> _editSettings() async {
    final s = ref.read(stringsProvider);
    final repo = ref.read(purchasingRepositoryProvider);
    final messenger = ScaffoldMessenger.of(context);
    try {
      final current = await repo.settings();
      if (!mounted) return;
      final lookback = TextEditingController(
        text: current.autoPoLookbackDays.toString(),
      );
      final trigger = TextEditingController(
        text: current.autoPoMinStockTrigger.toString(),
      );
      var autoPoEnabled = current.autoPoEnabled;
      final saved = await showDialog<bool>(
        context: context,
        builder: (dialogContext) => StatefulBuilder(
          builder: (dialogContext, setDialogState) => AlertDialog(
            title: Text(s.of('automationSettings')),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text(s.of('autoPoEnabled')),
                  value: autoPoEnabled,
                  onChanged: (v) =>
                      setDialogState(() => autoPoEnabled = v),
                ),
                TextField(
                  controller: lookback,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                    labelText: s.of('autoPoLookbackDays'),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: trigger,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                    labelText: s.of('autoPoMinStockTrigger'),
                  ),
                ),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(dialogContext, false),
                child: Text(s.of('cancel')),
              ),
              FilledButton(
                onPressed: () => Navigator.pop(dialogContext, true),
                child: Text(s.of('save')),
              ),
            ],
          ),
        ),
      );
      if (saved != true) {
        return;
      }
      await repo.updateSettings(
        PurchasingSettings(
          autoPoEnabled: autoPoEnabled,
          autoPoLookbackDays: int.tryParse(lookback.text) ?? 30,
          autoPoMinStockTrigger: int.tryParse(trigger.text) ?? 0,
        ),
      );
      messenger.showSnackBar(
        SnackBar(content: Text(s.of('autoPoSettingsSaved'))),
      );
    } catch (e) {
      messenger.showSnackBar(
        SnackBar(content: Text(friendlyError(e, s))),
      );
    }
  }

  /// True when the signed-in user may review (approve/reject) a document.
  ///
  /// Mirrors the backend rule: approvers can review any document except one
  /// they created themselves, unless they are a superuser.
  bool _canReview({required int ownerUserId}) {
    final auth = ref.read(authControllerProvider);
    if (!auth.has('purchasing:approve')) return false;
    if (auth.isSuperuser) return true;
    return ownerUserId != auth.userId;
  }

  Future<void> _editSupplier({Supplier? supplier}) async {
    final s = ref.read(stringsProvider);
    final name = TextEditingController(text: supplier?.name ?? '');
    final email = TextEditingController(text: supplier?.contactEmail ?? '');
    final phone = TextEditingController(text: supplier?.phone ?? '');
    final address = TextEditingController(text: supplier?.address ?? '');
    var isActive = supplier?.isActive ?? true;

    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: Text(
            supplier == null
                ? s.of('newSupplier')
                : s.of('editSupplier', args: {'name': supplier.name}),
          ),
          content: SizedBox(
            width: dialogWidth(context),
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(
                    controller: name,
                  decoration: InputDecoration(
                    labelText: s.of('supplierName'),
                    isDense: true,
                  ),
                ),
                TextField(
                  controller: email,
                  decoration: InputDecoration(
                    labelText: s.of('supplierEmail'),
                    isDense: true,
                  ),
                  keyboardType: TextInputType.emailAddress,
                ),
                TextField(
                  controller: phone,
                  decoration: InputDecoration(
                    labelText: s.of('supplierPhone'),
                    isDense: true,
                  ),
                ),
                TextField(
                  controller: address,
                  decoration: InputDecoration(
                    labelText: s.of('supplierAddress'),
                    isDense: true,
                  ),
                ),
                if (supplier != null)
                  SwitchListTile(
                    dense: true,
                    contentPadding: EdgeInsets.zero,
                    title: Text(s.of('staffActive')),
                    value: isActive,
                    onChanged: (v) => setDialogState(() => isActive = v),
                  ),
              ],
            ),
          ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(false),
              child: Text(s.of('cancel')),
            ),
            FilledButton(
              onPressed: () => Navigator.of(ctx).pop(true),
              child: Text(s.of('save')),
            ),
          ],
        ),
      ),
    );
    if (saved != true) return;
    final body = <String, dynamic>{
      if (name.text.trim().isNotEmpty) 'name': name.text.trim(),
      if (email.text.trim().isNotEmpty) 'contact_email': email.text.trim(),
      if (phone.text.trim().isNotEmpty) 'phone': phone.text.trim(),
      if (address.text.trim().isNotEmpty) 'address': address.text.trim(),
      if (supplier != null) 'is_active': isActive,
    };
    try {
      final repo = ref.read(purchasingRepositoryProvider);
      if (supplier == null) {
        await repo.createSupplier(body);
      } else {
        await repo.updateSupplier(supplier.id, body);
      }
      if (mounted) setState(_reload);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(friendlyError(e, s))));
      }
    }
  }

  Future<void> _createOrder() async {
    final s = ref.read(stringsProvider);
    final repo = ref.read(purchasingRepositoryProvider);
    final suppliers = await repo.suppliers();
    if (!mounted) return;
    final activeSuppliers =
        suppliers.where((sup) => sup.isActive).toList();
    if (activeSuppliers.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(s.of('noSuppliers'))),
      );
      return;
    }
    final products = await ref.read(catalogRepositoryProvider).products();
    if (!mounted) return;

    Supplier? supplier;
    final notes = TextEditingController();
    final lines = <({Product product, TextEditingController qty, TextEditingController cost})>[];
    for (final product in products) {
      lines.add((
        product: product,
        qty: TextEditingController(),
        cost: TextEditingController(text: '0'),
      ));
    }

    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: Text(s.of('newPurchaseOrder')),
          content: SizedBox(
            width: dialogWidth(context),
            height: 480,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                DropdownButtonFormField<int>(
                  initialValue: supplier?.id,
                  decoration: InputDecoration(
                    labelText: s.of('suppliers'),
                    isDense: true,
                  ),
                  items: [
                    for (final sup in activeSuppliers)
                      DropdownMenuItem<int>(
                        value: sup.id,
                        child: Text(sup.name),
                      ),
                  ],
                  onChanged: (v) => setDialogState(() {
                    supplier = activeSuppliers.firstWhere((sup) => sup.id == v);
                  }),
                ),
                TextField(
                  controller: notes,
                  decoration: InputDecoration(
                    labelText: s.of('adjustNote'),
                    isDense: true,
                  ),
                ),
                const Divider(height: 12),
                Expanded(
                  child: ListView(
                    children: [
                      for (final line in lines)
                        Row(
                          children: [
                            Expanded(
                              flex: 3,
                              child: Text(
                                line.product.name,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            SizedBox(
                              width: 90,
                              child: TextField(
                                controller: line.qty,
                                keyboardType: TextInputType.number,
                                decoration: InputDecoration(
                                  labelText: s.of('qtyOrdered'),
                                  isDense: true,
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            SizedBox(
                              width: 100,
                              child: TextField(
                                controller: line.cost,
                                keyboardType: TextInputType.number,
                                decoration: InputDecoration(
                                  labelText: s.of('unitCost'),
                                  isDense: true,
                                ),
                              ),
                            ),
                          ],
                        ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(false),
              child: Text(s.of('cancel')),
            ),
            FilledButton(
              onPressed: () => Navigator.of(ctx).pop(true),
              child: Text(s.of('createOrder')),
            ),
          ],
        ),
      ),
    );
    if (saved != true || supplier == null) return;
    final items = <Map<String, dynamic>>[];
    for (final line in lines) {
      final qty = int.tryParse(line.qty.text.trim());
      final cost = double.tryParse(line.cost.text.trim());
      if (qty == null || qty <= 0) continue;
      items.add({
        'product_id': line.product.id,
        'quantity_ordered': qty,
        'unit_cost': cost ?? 0,
      });
    }
    if (items.isEmpty) return;
    try {
      await repo.createOrder(
        supplierId: supplier!.id,
        items: items,
        notes: notes.text.trim().isEmpty ? null : notes.text.trim(),
      );
      await ref.read(catalogControllerProvider.notifier).refresh();
      if (mounted) {
        setState(_reload);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(s.of('purchaseOrders'))),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(friendlyError(e, s))));
      }
    }
  }

  Future<void> _orderDetail(PurchaseOrder order) async {
    final s = ref.read(stringsProvider);
    final suppliers = await ref.read(purchasingRepositoryProvider).suppliers();
    PurchaseOrderDetail? detail;
    try {
      detail = await ref.read(purchasingRepositoryProvider).orderDetail(order.id);
    } catch (_) {
      detail = null;
    }
    if (!mounted) return;
    final supplier = suppliers
        .where((sup) => sup.id == order.supplierId)
        .isEmpty
        ? null
        : suppliers.firstWhere((sup) => sup.id == order.supplierId);
    final auth = ref.read(authControllerProvider);
    final canApprove = auth.has('purchasing:approve');
    final canReview = _canReview(ownerUserId: order.userId);
    final rows = detail?.items ??
        order.items
            .map(
              (item) => PurchaseOrderItemDetail(
                id: item.id,
                purchaseOrderId: item.purchaseOrderId,
                productId: item.productId,
                quantityOrdered: item.quantityOrdered,
                quantityReceived: item.quantityReceived,
                unitCost: item.unitCost,
              ),
            )
            .toList();

    await showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('${s.of('purchaseOrders')} #${order.id}'),
        content: SizedBox(
          width: dialogWidth(context),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  '${supplier?.name ?? '—'} · ${order.status}',
                  style: Theme.of(ctx).textTheme.bodyMedium,
                ),
              ),
              const Divider(height: 12),
              Flexible(
                child: ListView(
                  shrinkWrap: true,
                  children: [
                    for (final item in rows)
                      ListTile(
                        dense: true,
                        contentPadding: EdgeInsets.zero,
                        title: Text('Product #${item.productId}'),
                        subtitle: Text(
                          '${s.of('qtyOrdered')}: ${item.quantityOrdered} · '
                          '${s.of('qtyReceived')}: ${item.quantityReceived} · '
                          '${s.of('qtyInvoiced')}: ${item.quantityInvoiced}',
                        ),
                        trailing: Text(
                          '${formatCents(centsFromApi(item.unitCost))}'
                          '${item.billedTotal > 0
                              ? ' · ${formatCents(centsFromApi(item.billedTotal))}'
                              : ''}',
                        ),
                      ),
                    if (detail != null) ...[
                      const Divider(height: 12),
                      Align(
                        alignment: Alignment.centerLeft,
                        child: Text(
                          s.of('timeline'),
                          style: Theme.of(ctx).textTheme.titleSmall,
                        ),
                      ),
                      for (final event in detail.timeline)
                        ListTile(
                          dense: true,
                          contentPadding: EdgeInsets.zero,
                          leading: const Icon(Icons.circle, size: 8),
                          title: Text(
                            event.note == null
                                ? event.event
                                : '${event.event} — ${event.note}',
                          ),
                          subtitle: event.at == null
                              ? null
                              : Text(formatDateTimeIso(event.at)),
                        ),
                      const Divider(height: 12),
                      Align(
                        alignment: Alignment.centerLeft,
                        child: Text(
                          '${s.of('receivedAmount')}: '
                          '${formatCents(centsFromApi(detail.totalReceivedAmount))}',
                        ),
                      ),
                      Align(
                        alignment: Alignment.centerLeft,
                        child: Text(
                          '${s.of('billedTotal')}: '
                          '${formatCents(centsFromApi(detail.totalBilledAmount))}',
                        ),
                      ),
                      Align(
                        alignment: Alignment.centerLeft,
                        child: Text(
                          '${s.of('outstandingPayable')}: '
                          '${formatCents(centsFromApi(detail.outstandingPayable))}',
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  '${s.of('estimatedTotal')}: '
                  '${formatCents(centsFromApi(order.totalEstimatedAmount))}',
                  style: Theme.of(ctx).textTheme.titleSmall,
                ),
              ),
              if (order.reviewNote != null)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      '${s.of('reviewNote')}: ${order.reviewNote}',
                      style: Theme.of(ctx).textTheme.bodySmall,
                    ),
                  ),
                ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: Text(s.of('done')),
          ),
          if (order.status == 'draft') ...[
            FilledButton(
              onPressed: () {
                Navigator.of(ctx).pop();
                _reviewOrder(order, action: 'submit');
              },
              child: Text(s.of('submitForReviewOrder')),
            ),
            TextButton(
              onPressed: () {
                Navigator.of(ctx).pop();
                _confirmCancelOrder(order);
              },
              child: Text(s.of('cancelOrder')),
            ),
          ],
          if (order.status == 'pending_review' && canReview) ...[
            FilledButton(
              onPressed: () {
                Navigator.of(ctx).pop();
                _reviewOrder(order, action: 'approve');
              },
              child: Text(s.of('approve')),
            ),
            TextButton(
              onPressed: () {
                Navigator.of(ctx).pop();
                _reviewOrder(order, action: 'reject');
              },
              child: Text(s.of('reject')),
            ),
          ],
          if (order.status == 'ordered' || order.status == 'partially_received')
            FilledButton(
              onPressed: () {
                Navigator.of(ctx).pop();
                _receiveDialog(order);
              },
              child: Text(s.of('receiveItems')),
            ),
          if (order.status == 'received' && canApprove)
            FilledButton(
              onPressed: () {
                Navigator.of(ctx).pop();
                _createInvoice(order);
              },
              child: Text(s.of('createInvoice')),
            ),
        ],
      ),
    );
  }

  Future<void> _reviewOrder(
    PurchaseOrder order, {
    required String action,
  }) async {
    final s = ref.read(stringsProvider);
    final note = TextEditingController();

    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(
          action == 'approve'
              ? s.of('approve')
              : action == 'reject'
              ? s.of('reject')
              : s.of('submitForReviewOrder'),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              action == 'approve'
                  ? s.of('confirmApproveOrder')
                  : action == 'reject'
                  ? s.of('confirmRejectOrder')
                  : s.of('confirmSubmitOrder'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: note,
              decoration: InputDecoration(
                labelText: s.of('reviewNote'),
                isDense: true,
              ),
              minLines: 1,
              maxLines: 3,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text(s.of('cancel')),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: Text(
              action == 'approve'
                  ? s.of('approve')
                  : action == 'reject'
                  ? s.of('reject')
                  : s.of('submitForReviewOrder'),
            ),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      final repo = ref.read(purchasingRepositoryProvider);
      final reviewNote = note.text.trim().isEmpty ? null : note.text.trim();
      switch (action) {
        case 'approve':
          await repo.markOrdered(order.id, reviewNote: reviewNote);
        case 'reject':
          await repo.rejectOrder(order.id, reviewNote: reviewNote);
        default:
          await repo.submitOrder(order.id, reviewNote: reviewNote);
      }
      if (mounted) setState(_reload);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(friendlyError(e, s))));
      }
    }
  }

  Future<void> _confirmCancelOrder(PurchaseOrder order) async {
    final s = ref.read(stringsProvider);
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(s.of('cancelOrder')),
        content: Text(s.of('confirmCancelOrder')),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text(s.of('no')),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: Text(s.of('yes')),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await ref.read(purchasingRepositoryProvider).cancelOrder(order.id);
      if (mounted) setState(_reload);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(friendlyError(e, s))));
      }
    }
  }

  Future<void> _receiveDialog(PurchaseOrder order) async {
    final s = ref.read(stringsProvider);
    final controllers = <int, TextEditingController>{};
    for (final item in order.items) {
      controllers[item.id] = TextEditingController(text: '${item.remaining}');
    }

    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('${s.of('receiveItems')} #${order.id}'),
        content: SizedBox(
          width: dialogWidth(context),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                s.of('confirmReceiveItems'),
                style: Theme.of(ctx).textTheme.bodySmall,
              ),
              const Divider(height: 12),
              Flexible(
                child: ListView(
                  shrinkWrap: true,
                  children: [
                    for (final item in order.items)
                      if (item.remaining > 0)
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                'Product #${item.productId}'
                                ' (${s.of('qtyOrdered')}: ${item.quantityOrdered})',
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            SizedBox(
                              width: 100,
                              child: TextField(
                                controller: controllers[item.id],
                                keyboardType: TextInputType.number,
                                decoration: InputDecoration(
                                  labelText: s.of('qtyReceived'),
                                  isDense: true,
                                ),
                              ),
                            ),
                          ],
                        ),
                  ],
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text(s.of('cancel')),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: Text(s.of('receive')),
          ),
        ],
      ),
    );
    if (ok != true) return;
    final items = <Map<String, dynamic>>[];
    for (final item in order.items) {
      final qty = int.tryParse(controllers[item.id]!.text.trim());
      if (qty == null || qty <= 0) continue;
      items.add({
        'purchase_order_item_id': item.id,
        'quantity_received': qty,
      });
    }
    if (items.isEmpty) return;
    try {
      await ref.read(purchasingRepositoryProvider).receiveItems(order.id, items);
      await ref.read(catalogControllerProvider.notifier).refresh();
      if (mounted) setState(_reload);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(friendlyError(e, s))));
      }
    }
  }

  Future<void> _createInvoice(PurchaseOrder order) async {
    final s = ref.read(stringsProvider);
    final invoiceNumber = TextEditingController();
    final invoiceDate = DateTime.now();
    DateTime? dueDate;
    final lines = <
        ({
          PurchaseOrderItem item,
          TextEditingController qty,
          TextEditingController cost,
        })>[];
    for (final item in order.items) {
      if (item.quantityReceived > 0) {
        lines.add((
          item: item,
          qty: TextEditingController(text: '${item.quantityReceived}'),
          cost: TextEditingController(text: _num(item.unitCost)),
        ));
      }
    }
    if (lines.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(s.of('noEligiblePo'))),
      );
      return;
    }

    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: Text(s.of('createInvoice')),
          content: SizedBox(
            width: dialogWidth(context),
            height: 460,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  '${s.of('purchaseOrders')} #${order.id} · '
                  '${lines.length} ${s.of('itemsCount', args: {'count': lines.length})}',
                ),
                TextField(
                  controller: invoiceNumber,
                  decoration: InputDecoration(
                    labelText: s.of('invoiceNumber'),
                    isDense: true,
                  ),
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        onPressed: () async {
                          final picked = await showDatePicker(
                            context: ctx,
                            initialDate: invoiceDate,
                            firstDate: DateTime(2020),
                            lastDate: DateTime(2100),
                          );
                          if (picked != null) {
                            setDialogState(() => dueDate = picked);
                          }
                        },
                        child: Text(
                          '${s.of('dueDate')}: '
                          '${dueDate == null ? '-' : formatDateTime(dueDate!, overrideFormat: 'yyyy-MM-dd')}',
                        ),
                      ),
                    ),
                  ],
                ),
                const Divider(height: 12),
                Expanded(
                  child: ListView(
                    children: [
                      for (final line in lines)
                        Row(
                          children: [
                            Expanded(
                              flex: 3,
                              child: Text(
                                'Product #${line.item.productId}'
                                ' (${s.of('qtyReceived')}: ${line.item.quantityReceived})',
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            SizedBox(
                              width: 90,
                              child: TextField(
                                controller: line.qty,
                                keyboardType: TextInputType.number,
                                decoration: InputDecoration(
                                  labelText: s.of('billed'),
                                  isDense: true,
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            SizedBox(
                              width: 100,
                              child: TextField(
                                controller: line.cost,
                                keyboardType: TextInputType.number,
                                decoration: InputDecoration(
                                  labelText: s.of('unitCost'),
                                  isDense: true,
                                ),
                              ),
                            ),
                          ],
                        ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(false),
              child: Text(s.of('cancel')),
            ),
            FilledButton(
              onPressed: () => Navigator.of(ctx).pop(true),
              child: Text(s.of('createInvoice')),
            ),
          ],
        ),
      ),
    );
    if (ok != true || invoiceNumber.text.trim().isEmpty) return;
    final items = <Map<String, dynamic>>[];
    for (final line in lines) {
      final qty = int.tryParse(line.qty.text.trim());
      final cost = double.tryParse(line.cost.text.trim());
      if (qty == null || qty <= 0) continue;
      items.add({
        'purchase_order_item_id': line.item.id,
        'billed_quantity': qty,
        'billed_unit_cost': cost ?? line.item.unitCost,
      });
    }
    if (items.isEmpty) return;
    try {
      await ref.read(purchasingRepositoryProvider).createInvoice({
        'purchase_order_id': order.id,
        'invoice_number': invoiceNumber.text.trim(),
        'invoice_date': invoiceDate.toUtc().toIso8601String(),
        if (dueDate != null) 'due_date': dueDate!.toUtc().toIso8601String(),
        'items': items,
      });
      if (mounted) setState(_reload);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(friendlyError(e, s))));
      }
    }
  }

  String _num(double value) =>
      value == value.roundToDouble() ? '${value.round()}' : '$value';

  Future<void> _invoiceDetail(PurchaseInvoice invoice) async {
    final s = ref.read(stringsProvider);
    final suppliers = await ref.read(purchasingRepositoryProvider).suppliers();
    if (!mounted) return;
    final supplier = suppliers
        .where((sup) => sup.id == invoice.supplierId)
        .isEmpty
        ? null
        : suppliers.firstWhere((sup) => sup.id == invoice.supplierId);
    final canReview = _canReview(ownerUserId: invoice.userId);

    await showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('${invoice.invoiceNumber} · ${invoice.status}'),
        content: SizedBox(
          width: dialogWidth(context),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  '${supplier?.name ?? '—'} · PO #${invoice.purchaseOrderId}',
                  style: Theme.of(ctx).textTheme.bodyMedium,
                ),
              ),
              if (invoice.hasQuantityVariance || invoice.hasPriceVariance)
                Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      '${s.of('variance')}: '
                      '${invoice.hasQuantityVariance ? s.of('quantityVariance') : ''}'
                      '${invoice.hasQuantityVariance && invoice.hasPriceVariance ? ' · ' : ''}'
                      '${invoice.hasPriceVariance ? s.of('priceVariance') : ''}'
                      ' (${formatCents(centsFromApi(invoice.varianceAmount))})',
                      style: Theme.of(ctx).textTheme.bodySmall?.copyWith(
                        color: Theme.of(ctx).colorScheme.error,
                      ),
                    ),
                  ),
                ),
              const Divider(height: 12),
              Flexible(
                child: ListView(
                  shrinkWrap: true,
                  children: [
                    for (final item in invoice.items)
                      ListTile(
                        dense: true,
                        contentPadding: EdgeInsets.zero,
                        title: Text('Product #${item.productId}'),
                        subtitle: Text(
                          '${s.of('billed')}: ${item.billedQuantity} × '
                          '${formatCents(centsFromApi(item.billedUnitCost))}',
                        ),
                        trailing: Text(formatCents(centsFromApi(item.lineTotal))),
                      ),
                  ],
                ),
              ),
              Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  '${s.of('estimatedTotal')}: ${formatCents(centsFromApi(invoice.totalAmount))}',
                  style: Theme.of(ctx).textTheme.titleSmall,
                ),
              ),
              if (invoice.reviewNote != null)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      '${s.of('reviewNote')}: ${invoice.reviewNote}',
                      style: Theme.of(ctx).textTheme.bodySmall,
                    ),
                  ),
                ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: Text(s.of('done')),
          ),
          if (invoice.status == 'draft')
            FilledButton(
              onPressed: () {
                Navigator.of(ctx).pop();
                _reviewInvoice(invoice, action: 'submit');
              },
              child: Text(s.of('submitForReview')),
            ),
          if (invoice.status == 'pending_review' && canReview) ...[
            TextButton(
              onPressed: () {
                Navigator.of(ctx).pop();
                _reviewInvoice(invoice, action: 'approve');
              },
              child: Text(s.of('approve')),
            ),
            TextButton(
              onPressed: () {
                Navigator.of(ctx).pop();
                _reviewInvoice(invoice, action: 'reject');
              },
              child: Text(s.of('reject')),
            ),
          ],
        ],
      ),
    );
  }

  Future<void> _reviewInvoice(PurchaseInvoice invoice, {required String action}) async {
    final s = ref.read(stringsProvider);
    final note = TextEditingController();

    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(
          action == 'approve' ? s.of('approve') : action == 'reject' ? s.of('reject') : s.of('submitForReview'),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              action == 'approve'
                  ? s.of('confirmApprove')
                  : action == 'reject'
                  ? s.of('confirmReject')
                  : '${invoice.invoiceNumber} — ${s.of('submitForReview')}',
            ),
            const SizedBox(height: 12),
            TextField(
              controller: note,
              decoration: InputDecoration(
                labelText: s.of('reviewNote'),
                isDense: true,
              ),
              minLines: 1,
              maxLines: 3,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text(s.of('cancel')),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: Text(
              action == 'approve'
                  ? s.of('approve')
                  : action == 'reject'
                  ? s.of('reject')
                  : s.of('submitForReview'),
            ),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      final repo = ref.read(purchasingRepositoryProvider);
      final reviewNote = note.text.trim().isEmpty ? null : note.text.trim();
      switch (action) {
        case 'approve':
          await repo.approveInvoice(invoice.id, reviewNote: reviewNote);
        case 'reject':
          await repo.rejectInvoice(invoice.id, reviewNote: reviewNote);
        default:
          await repo.submitInvoice(invoice.id, reviewNote: reviewNote);
      }
      if (mounted) setState(_reload);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(friendlyError(e, s))));
      }
    }
  }

  Future<void> _createPayment() async {
    final s = ref.read(stringsProvider);
    final repo = ref.read(purchasingRepositoryProvider);
    final suppliers = await repo.suppliers();
    final invoices = await repo.invoices(status: 'approved');
    if (!mounted) return;
    final payableInvoices = invoices
        .where((inv) => inv.outstandingAmount > 0)
        .toList();
    final activeSuppliers =
        suppliers.where((sup) => sup.isActive).toList();
    if (activeSuppliers.isEmpty || payableInvoices.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(s.of('noApprovedInvoices'))),
      );
      return;
    }

    Supplier? supplier;
    PurchaseInvoice? invoice;
    final amount = TextEditingController();
    final reference = TextEditingController();
    var paymentMethod = 'cash';

    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: Text(s.of('createPayment')),
          content: SizedBox(
            width: dialogWidth(context),
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  DropdownButtonFormField<int>(
                    initialValue: supplier?.id,
                    decoration: InputDecoration(
                    labelText: s.of('suppliers'),
                    isDense: true,
                  ),
                  items: [
                    for (final sup in activeSuppliers)
                      DropdownMenuItem<int>(
                        value: sup.id,
                        child: Text(sup.name),
                      ),
                  ],
                  onChanged: (v) => setDialogState(() {
                    supplier = activeSuppliers.firstWhere((sup) => sup.id == v);
                    invoice = null;
                  }),
                ),
                DropdownButtonFormField<int>(
                  initialValue: invoice?.id,
                  decoration: InputDecoration(
                    labelText: s.of('selectApprovedInvoice'),
                    isDense: true,
                  ),
                  items: [
                    for (final inv in payableInvoices)
                      if (inv.supplierId == supplier?.id)
                        DropdownMenuItem<int>(
                          value: inv.id,
                          child: Text(
                            '${inv.invoiceNumber} · '
                            '${formatCents(centsFromApi(inv.totalAmount))}'
                            ' · ${s.of('outstanding')}: '
                            '${formatCents(centsFromApi(inv.outstandingAmount))}',
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                  ],
                  onChanged: (v) => setDialogState(() {
                    invoice = payableInvoices.firstWhere((inv) => inv.id == v);
                  }),
                ),
                TextField(
                  controller: amount,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                    labelText: s.of('paymentAmount'),
                    isDense: true,
                  ),
                ),
                DropdownButtonFormField<String>(
                  initialValue: paymentMethod,
                  decoration: InputDecoration(
                    labelText: s.of('paymentMethod'),
                    isDense: true,
                  ),
                  items: [
                    for (final method in const [
                      'cash',
                      'transfer',
                      'card',
                      'mobile',
                    ])
                      DropdownMenuItem(
                        value: method,
                        child: Text(paymentMethodLabel(s, method)),
                      ),
                  ],
                  onChanged: (v) => setDialogState(() {
                    paymentMethod = v!;
                  }),
                ),
                TextField(
                  controller: reference,
                  decoration: InputDecoration(
                    labelText: s.of('paymentReference'),
                    isDense: true,
                  ),
                ),
              ],
            ),
          ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(false),
              child: Text(s.of('cancel')),
            ),
            FilledButton(
              onPressed: () => Navigator.of(ctx).pop(true),
              child: Text(s.of('createPayment')),
            ),
          ],
        ),
      ),
    );
    if (saved != true || supplier == null || invoice == null) return;
    final amountValue = double.tryParse(amount.text.trim());
    if (amountValue == null || amountValue <= 0) return;
    try {
      await repo.createPayment({
        'supplier_id': supplier!.id,
        'invoice_id': invoice!.id,
        'amount': amountValue,
        'payment_method': paymentMethod,
        if (reference.text.trim().isNotEmpty)
          'reference': reference.text.trim(),
      });
      if (mounted) {
        setState(_reload);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(s.of('supplierPayments'))),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(friendlyError(e, s))));
      }
    }
  }

  Future<void> _paymentDetail(SupplierPayment payment) async {
    final s = ref.read(stringsProvider);
    final suppliers = await ref.read(purchasingRepositoryProvider).suppliers();
    if (!mounted) return;
    final supplier = suppliers
        .where((sup) => sup.id == payment.supplierId)
        .isEmpty
        ? null
        : suppliers.firstWhere((sup) => sup.id == payment.supplierId);
    final canReview = _canReview(ownerUserId: payment.userId);

    await showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('#${payment.id} · ${payment.status}'),
        content: SizedBox(
          width: dialogWidth(context),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  '${supplier?.name ?? '—'} · '
                  '${s.of('paymentMethod')}: ${paymentMethodLabel(s, payment.paymentMethod)}'
                  '${payment.reference != null ? ' · ${payment.reference}' : ''}',
                  style: Theme.of(ctx).textTheme.bodyMedium,
                ),
              ),
              const Divider(height: 12),
              Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  '${s.of('invoiceNumber')} #${payment.invoiceId} · '
                  '${formatCents(centsFromApi(payment.amount))}',
                  style: Theme.of(ctx).textTheme.titleSmall,
                ),
              ),
              if (payment.reviewNote != null)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      '${s.of('reviewNote')}: ${payment.reviewNote}',
                      style: Theme.of(ctx).textTheme.bodySmall,
                    ),
                  ),
                ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: Text(s.of('done')),
          ),
          if (payment.status == 'draft')
            FilledButton(
              onPressed: () {
                Navigator.of(ctx).pop();
                _reviewPayment(payment, action: 'submit');
              },
              child: Text(s.of('submitForReview')),
            ),
          if (payment.status == 'pending_review' && canReview) ...[
            TextButton(
              onPressed: () {
                Navigator.of(ctx).pop();
                _reviewPayment(payment, action: 'approve');
              },
              child: Text(s.of('approve')),
            ),
            TextButton(
              onPressed: () {
                Navigator.of(ctx).pop();
                _reviewPayment(payment, action: 'reject');
              },
              child: Text(s.of('reject')),
            ),
          ],
        ],
      ),
    );
  }

  Future<void> _reviewPayment(
    SupplierPayment payment, {
    required String action,
  }) async {
    final s = ref.read(stringsProvider);
    final note = TextEditingController();

    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(
          action == 'approve'
              ? s.of('approve')
              : action == 'reject'
              ? s.of('reject')
              : s.of('submitForReview'),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              action == 'approve'
                  ? s.of('confirmApprovePayment')
                  : action == 'reject'
                  ? s.of('confirmRejectPayment')
                  : s.of('confirmSubmitPayment'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: note,
              decoration: InputDecoration(
                labelText: s.of('reviewNote'),
                isDense: true,
              ),
              minLines: 1,
              maxLines: 3,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text(s.of('cancel')),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: Text(
              action == 'approve'
                  ? s.of('approve')
                  : action == 'reject'
                  ? s.of('reject')
                  : s.of('submitForReview'),
            ),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      final repo = ref.read(purchasingRepositoryProvider);
      final reviewNote =
          note.text.trim().isEmpty ? null : note.text.trim();
      switch (action) {
        case 'approve':
          await repo.approvePayment(payment.id, reviewNote: reviewNote);
        case 'reject':
          await repo.rejectPayment(payment.id, reviewNote: reviewNote);
        default:
          await repo.submitPayment(payment.id, reviewNote: reviewNote);
      }
      if (mounted) setState(_reload);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(friendlyError(e, s))));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    final canManage = ref.watch(authControllerProvider).has('purchasing:manage');

    return Scaffold(
      appBar: AppBar(
        title: Text(s.of('purchasing')),
        actions: [
          if (canManage)
            IconButton(
              tooltip: s.of('automationSettings'),
              icon: const Icon(Icons.settings_outlined),
              onPressed: () => _editSettings(),
            ),
          IconButton(
            tooltip: s.of('inventory'),
            icon: const Icon(Icons.refresh),
            onPressed: () => setState(_reload),
          ),
        ],
      ),
      floatingActionButton: _tab == 0
          ? FloatingActionButton(
              onPressed: () => _editSupplier(),
              child: const Icon(Icons.add),
            )
          : _tab == 1
          ? (canManage
              ? FloatingActionButton(
                  onPressed: _createOrder,
                  child: const Icon(Icons.add),
                )
              : null)
          : _tab == 3
          ? (canManage
              ? FloatingActionButton(
                  onPressed: _createPayment,
                  child: const Icon(Icons.add),
                )
              : null)
          : null,
      body: Column(
        children: [
          SegmentedButton<int>(
            segments: [
              ButtonSegment(
                value: 0,
                label: Text(s.of('suppliers')),
                icon: const Icon(Icons.factory_outlined, size: 16),
              ),
              ButtonSegment(
                value: 1,
                label: Text(s.of('purchaseOrders')),
                icon: const Icon(Icons.shopping_cart_outlined, size: 16),
              ),
              ButtonSegment(
                value: 2,
                label: Text(s.of('purchaseInvoices')),
                icon: const Icon(Icons.receipt_outlined, size: 16),
              ),
              ButtonSegment(
                value: 3,
                label: Text(s.of('supplierPayments')),
                icon: const Icon(Icons.payments_outlined, size: 16),
              ),
              ButtonSegment(
                value: 4,
                label: Text(s.of('ledger')),
                icon: const Icon(Icons.menu_book_outlined, size: 16),
              ),
            ],
            selected: {_tab},
            onSelectionChanged: (v) => setState(() => _tab = v.first),
          ),
          Expanded(
            child: switch (_tab) {
              0 => _suppliersView(context, s),
              1 => _ordersView(context, s, canManage),
              2 => _invoicesView(context, s),
              4 => _ledgerView(context, s),
              _ => _paymentsView(context, s),
            },
          ),
        ],
      ),
    );
  }

  Widget _ledgerView(BuildContext context, AppStrings s) {
    return FutureBuilder<List<Supplier>>(
      future: _suppliers,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return Center(child: Text(friendlyError(snapshot.error!, s)));
        }
        final suppliers = snapshot.data ?? [];
        if (suppliers.isEmpty) {
          return Center(child: Text(s.of('noSuppliers')));
        }
        return ListView.separated(
          padding: const EdgeInsets.all(16),
          itemCount: suppliers.length,
          separatorBuilder: (_, _) => const Divider(height: 8),
          itemBuilder: (context, i) {
            final supplier = suppliers[i];
            return ListTile(
              leading: const Icon(Icons.menu_book_outlined),
              title: Text(supplier.name),
              subtitle: Text(supplier.contactEmail ?? supplier.phone ?? '—'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => _supplierLedger(supplier),
            );
          },
        );
      },
    );
  }

  Future<void> _supplierLedger(Supplier supplier) async {
    final s = ref.read(stringsProvider);
    final SupplierLedger ledger;
    try {
      ledger = await ref
          .read(purchasingRepositoryProvider)
          .supplierLedger(supplier.id);
    } catch (err) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(friendlyError(err, s))),
      );
      return;
    }
    if (!mounted) return;
    await showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('${s.of('ledger')} · ${ledger.supplierName}'),
        content: SizedBox(
          width: dialogWidth(context),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _ledgerRow(
                  s.of('openPurchaseOrders'),
                  '${ledger.openPurchaseOrders} · '
                      '${formatCents(centsFromApi(ledger.openPoAmount))}',
                ),
                _ledgerRow(
                  s.of('pendingInvoices'),
                  '${ledger.pendingInvoiceCount} · '
                      '${formatCents(centsFromApi(ledger.pendingInvoiceAmount))}',
                ),
                _ledgerRow(
                  s.of('approvedInvoices'),
                  formatCents(centsFromApi(ledger.approvedInvoiceTotal)),
                ),
                _ledgerRow(
                  s.of('approvedPayments'),
                  formatCents(centsFromApi(ledger.approvedPaymentTotal)),
                ),
                _ledgerRow(
                  s.of('outstandingPayable'),
                  formatCents(centsFromApi(ledger.outstandingPayable)),
                ),
                const Divider(height: 16),
                for (final entry in ledger.entries)
                  ListTile(
                    dense: true,
                    contentPadding: EdgeInsets.zero,
                    leading: Icon(_ledgerIcon(entry.kind), size: 18),
                    title: Text(entry.reference ?? '#${entry.id}'),
                    subtitle: Text(
                      '${entry.kind} · ${entry.status}'
                      '${entry.date != null ? ' · ${formatDateTimeIso(entry.date)}' : ''}',
                    ),
                    trailing: Text(formatCents(centsFromApi(entry.amount))),
                  ),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: Text(s.of('done')),
          ),
        ],
      ),
    );
  }

  IconData _ledgerIcon(String kind) {
    return switch (kind) {
      'purchase_order' => Icons.shopping_cart_outlined,
      'invoice' => Icons.receipt_outlined,
      _ => Icons.payments_outlined,
    };
  }

  Widget _ledgerRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        children: [
          Expanded(child: Text(label)),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }

  Widget _suppliersView(BuildContext context, AppStrings s) {
    return FutureBuilder<List<Supplier>>(
      future: _suppliers,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return Center(child: Text(friendlyError(snapshot.error!, s)));
        }
        final suppliers = snapshot.data ?? [];
        if (suppliers.isEmpty) {
          return Center(child: Text(s.of('noSuppliers')));
        }
        return ListView.separated(
          padding: const EdgeInsets.all(16),
          itemCount: suppliers.length,
          separatorBuilder: (_, _) => const Divider(height: 8),
          itemBuilder: (context, i) {
            final supplier = suppliers[i];
            return ListTile(
              leading: const Icon(Icons.factory_outlined),
              title: Text(
                '${supplier.name}${supplier.isActive ? '' : ' (${s.of('staffInactive')})'}',
              ),
              subtitle: Text(
                [
                  if (supplier.contactEmail != null) supplier.contactEmail!,
                  if (supplier.phone != null) supplier.phone!,
                ].join(' · '),
              ),
              trailing: IconButton(
                tooltip: s.of('editSupplier', args: {'name': supplier.name}),
                icon: const Icon(Icons.edit_outlined),
                onPressed: () => _editSupplier(supplier: supplier),
              ),
              onTap: () => _editSupplier(supplier: supplier),
            );
          },
        );
      },
    );
  }

  Widget _statusChips({
    required String? current,
    required List<String> statuses,
    required void Function(String?) onChanged,
  }) {
    return SizedBox(
      height: 44,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 8),
        children: [
          for (final status in statuses)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: ChoiceChip(
                label: Text(status),
                selected: current == status,
                onSelected: (_) => onChanged(status),
              ),
            ),
        ],
      ),
    );
  }

  Widget _ordersView(BuildContext context, AppStrings s, bool canManage) {
    return Column(
      children: [
        _statusChips(
          current: _orderStatus,
          statuses: const [
            'draft',
            'pending_review',
            'ordered',
            'partially_received',
            'received',
            'rejected',
            'cancelled',
          ],
          onChanged: (v) => setState(() {
            _orderStatus = v;
            _reload();
          }),
        ),
        Expanded(
          child: FutureBuilder<List<PurchaseOrder>>(
            future: _orders,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snapshot.hasError) {
                return ErrorStateView(
                  message: friendlyError(snapshot.error!, s),
                  onRetry: _reload,
                );
              }
              final orders = snapshot.data ?? [];
              if (orders.isEmpty) {
                return EmptyStateView(message: s.of('noPurchaseOrders'));
              }
              return RefreshIndicator(
                onRefresh: _refresh,
                child: ListView.separated(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.all(16),
                  itemCount: orders.length,
                  separatorBuilder: (_, _) => const Divider(height: 8),
                  itemBuilder: (context, i) {
                    final order = orders[i];
                    return Card(
                      margin: EdgeInsets.zero,
                      child: ListTile(
                        title: Text('PO #${order.id} · ${order.status}'),
                        subtitle: Text(
                          '${order.items.length} ${s.of('itemsCount', args: {'count': order.items.length})} · '
                          '${formatCents(centsFromApi(order.totalEstimatedAmount))}'
                          '${order.createdAt != null ? ' · ${formatDateTimeIso(order.createdAt)}' : ''}',
                        ),
                        trailing: IconButton(
                          tooltip: s.of('purchaseOrders'),
                          icon: const Icon(Icons.chevron_right),
                          onPressed: () => _orderDetail(order),
                        ),
                        onTap: () => _orderDetail(order),
                      ),
                    );
                  },
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _invoicesView(BuildContext context, AppStrings s) {
    return Column(
      children: [
        _statusChips(
          current: _invoiceStatus,
          statuses: const ['draft', 'pending_review', 'approved', 'rejected'],
          onChanged: (v) => setState(() {
            _invoiceStatus = v;
            _reload();
          }),
        ),
        Expanded(
          child: FutureBuilder<List<PurchaseInvoice>>(
            future: _invoices,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snapshot.hasError) {
                return ErrorStateView(
                  message: friendlyError(snapshot.error!, s),
                  onRetry: _reload,
                );
              }
              final invoices = snapshot.data ?? [];
              if (invoices.isEmpty) {
                return EmptyStateView(message: s.of('noInvoices'));
              }
              return RefreshIndicator(
                onRefresh: _refresh,
                child: ListView.separated(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.all(16),
                  itemCount: invoices.length,
                  separatorBuilder: (_, _) => const Divider(height: 8),
                  itemBuilder: (context, i) {
                    final invoice = invoices[i];
                    return Card(
                      margin: EdgeInsets.zero,
                      child: ListTile(
                        title: Text(
                          '${invoice.invoiceNumber} · ${invoice.status}',
                        ),
                        subtitle: Text(
                          'PO #${invoice.purchaseOrderId} · '
                          '${formatCents(centsFromApi(invoice.totalAmount))}'
                          '${(invoice.hasQuantityVariance || invoice.hasPriceVariance) ? ' · ${s.of('variance')}' : ''}',
                        ),
                        trailing: IconButton(
                          tooltip: s.of('purchaseInvoices'),
                          icon: const Icon(Icons.chevron_right),
                          onPressed: () => _invoiceDetail(invoice),
                        ),
                        onTap: () => _invoiceDetail(invoice),
                      ),
                    );
                  },
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _paymentsView(BuildContext context, AppStrings s) {
    return Column(
      children: [
        _statusChips(
          current: _paymentStatus,
          statuses: const ['draft', 'pending_review', 'approved', 'rejected'],
          onChanged: (v) => setState(() {
            _paymentStatus = v;
            _reload();
          }),
        ),
        Expanded(
          child: FutureBuilder<List<SupplierPayment>>(
            future: _payments,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snapshot.hasError) {
                return ErrorStateView(
                  message: friendlyError(snapshot.error!, s),
                  onRetry: _reload,
                );
              }
              final payments = snapshot.data ?? [];
              if (payments.isEmpty) {
                return EmptyStateView(message: s.of('noPayments'));
              }
              return RefreshIndicator(
                onRefresh: _refresh,
                child: ListView.separated(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.all(16),
                  itemCount: payments.length,
                  separatorBuilder: (_, _) => const Divider(height: 8),
                  itemBuilder: (context, i) {
                    final payment = payments[i];
                    return Card(
                      margin: EdgeInsets.zero,
                      child: ListTile(
                        title: Text('#${payment.id} · ${payment.status}'),
                        subtitle: Text(
                          '${s.of('invoiceNumber')} #${payment.invoiceId} · '
                          '${formatCents(centsFromApi(payment.amount))} · '
                          '${paymentMethodLabel(s, payment.paymentMethod)}'
                          '${payment.reference != null ? ' · ${payment.reference}' : ''}',
                        ),
                        trailing: IconButton(
                          tooltip: s.of('supplierPayments'),
                          icon: const Icon(Icons.chevron_right),
                          onPressed: () => _paymentDetail(payment),
                        ),
                        onTap: () => _paymentDetail(payment),
                      ),
                    );
                  },
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

/// Localized label for a supplier payment method.
String paymentMethodLabel(AppStrings s, String method) {
  switch (method) {
    case 'transfer':
      return s.of('payTransfer');
    case 'card':
      return s.of('payCard');
    case 'mobile':
      return s.of('payMobile');
    default:
      return s.of('payCash');
  }
}
