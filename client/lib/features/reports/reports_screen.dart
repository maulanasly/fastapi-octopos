/// Reports screen: sales summary, daily close, low stock, shift reports.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/dates.dart';
import '../../core/money.dart';
import '../../core/models.dart';
import '../../core/strings.dart';

class ReportsScreen extends ConsumerStatefulWidget {
  const ReportsScreen({super.key});

  @override
  ConsumerState<ReportsScreen> createState() => _ReportsScreenState();
}

class _ReportsScreenState extends ConsumerState<ReportsScreen> {
  String _period = 'today';
  late Future<SalesSummary> _salesFuture;
  late Future<List<Product>> _lowStockFuture;
  late Future<DailyCloseTotals> _dailyCloseFuture;
  late Future<List<DailyShiftItem>> _shiftsFuture;
  late Future<List<TopProductItem>> _topProductsFuture;
  late Future<List<CategorySalesItem>> _categorySalesFuture;

  @override
  void initState() {
    super.initState();
    _load();
  }

  (String?, String?) _datesFor(String period) {
    final now = DateTime.now();
    switch (period) {
      case 'today':
        final start = DateTime(now.year, now.month, now.day);
        return (
          start.toUtc().toIso8601String(),
          now.toUtc().toIso8601String(),
        );
      case '7d':
        return (
          now.subtract(const Duration(days: 7)).toUtc().toIso8601String(),
          now.toUtc().toIso8601String(),
        );
      case '30d':
        return (
          now.subtract(const Duration(days: 30)).toUtc().toIso8601String(),
          now.toUtc().toIso8601String(),
        );
      default:
        return (null, null);
    }
  }

  void _load() {
    final repo = ref.read(reportRepositoryProvider);
    final (startDate, endDate) = _datesFor(_period);
    _salesFuture = repo.sales(startDate: startDate, endDate: endDate);
    _lowStockFuture = repo.lowStock();
    _dailyCloseFuture = repo.dailyClose();
    _shiftsFuture = repo.shifts();
    _topProductsFuture = repo.topProducts(
      startDate: startDate,
      endDate: endDate,
    );
    _categorySalesFuture = repo.categorySales(
      startDate: startDate,
      endDate: endDate,
    );
  }

  Future<void> _showShiftReport(DailyShiftItem shift) async {
    final s = ref.read(stringsProvider);
    final report = await ref
        .read(reportRepositoryProvider)
        .shiftReport(shift.reconciliationId);
    if (!mounted) return;
    await showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('${s.of('shifts')} #${report.reconciliationId}'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                '${s.of('operator')}: ${report.operatorName ?? '-'}',
                style: Theme.of(ctx).textTheme.bodySmall,
              ),
              Text(
                '${s.of('date')}: ${formatDateTimeIso(report.closedAt)}',
                style: Theme.of(ctx).textTheme.bodySmall,
              ),
              const Divider(height: 20),
              _dialogRow(ctx, s.of('grossRevenue'), report.grossSalesTotal),
              _dialogRow(ctx, s.of('netRevenue'), report.netSalesTotal),
              _dialogRow(ctx, s.of('cashSales'), report.cashSalesTotal),
              _dialogRow(ctx, s.of('nonCashSales'), report.nonCashSalesTotal),
              _dialogRow(ctx, s.of('refunds'), report.refundsTotal),
              _dialogRow(
                ctx,
                s.of('orders'),
                report.completedOrderCount.toDouble(),
              ),
              _dialogRow(
                ctx,
                s.of('variance'),
                report.cashVariance,
                highlight: report.cashVariance != 0,
              ),
              const Divider(height: 20),
              for (final p in report.paymentBreakdown)
                _dialogRow(ctx, p.paymentMethod, p.amount),
            ],
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

  Widget _dialogRow(
    BuildContext context,
    String label,
    double amount, {
    bool highlight = false,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        children: [
          Expanded(child: Text(label)),
          Text(
            formatCents(centsFromApi(amount)),
            style: TextStyle(
              fontWeight: highlight ? FontWeight.bold : FontWeight.w500,
              color: highlight ? Theme.of(context).colorScheme.error : null,
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final strings = ref.watch(stringsProvider);
    return Scaffold(
      appBar: AppBar(
        title: Text(strings.of('reports')),
        actions: [
          IconButton(
            onPressed: () => setState(_load),
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          SegmentedButton<String>(
            segments: [
              ButtonSegment(
                value: 'today',
                label: Text(strings.of('periodToday')),
              ),
              ButtonSegment(value: '7d', label: Text(strings.of('period7d'))),
              ButtonSegment(value: '30d', label: Text(strings.of('period30d'))),
              ButtonSegment(value: 'all', label: Text(strings.of('periodAll'))),
            ],
            selected: {_period},
            onSelectionChanged: (v) => setState(() {
              _period = v.first;
              _load();
            }),
          ),
          const SizedBox(height: 16),
          FutureBuilder<SalesSummary>(
            future: _salesFuture,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const Padding(
                  padding: EdgeInsets.all(32),
                  child: Center(child: CircularProgressIndicator()),
                );
              }
              if (snapshot.hasError) {
                return Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Text('Sales data unavailable:\n${snapshot.error}'),
                  ),
                );
              }
              final s = snapshot.data!;
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        'Sales summary',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 12),
                      _metric(
                        context,
                        'Gross revenue',
                        formatCents(centsFromApi(s.grossRevenue)),
                      ),
                      _metric(
                        context,
                        'Discounts',
                        formatCents(centsFromApi(s.totalDiscounts)),
                      ),
                      _metric(
                        context,
                        'Refunds',
                        formatCents(centsFromApi(s.totalRefunds)),
                      ),
                      _metric(
                        context,
                        'Net revenue',
                        formatCents(centsFromApi(s.netRevenue)),
                      ),
                      _metric(context, strings.of('orders'), '${s.orderCount}'),
                      _metric(
                        context,
                        'Avg order',
                        formatCents(centsFromApi(s.averageOrderValue)),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
          const SizedBox(height: 16),
          FutureBuilder<List<TopProductItem>>(
            future: _topProductsFuture,
            builder: (context, snapshot) {
              final items = snapshot.data ?? [];
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        strings.of('topProducts'),
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 8),
                      if (items.isEmpty)
                        Text(strings.of('noOrders'))
                      else
                        for (final item in items)
                          ListTile(
                            dense: true,
                            contentPadding: EdgeInsets.zero,
                            title: Text(item.productName),
                            subtitle: Text(
                              '${item.totalQuantitySold} × ${item.productSku}',
                            ),
                            trailing: Text(
                              formatCents(centsFromApi(item.totalRevenue)),
                            ),
                          ),
                    ],
                  ),
                ),
              );
            },
          ),
          const SizedBox(height: 16),
          FutureBuilder<List<CategorySalesItem>>(
            future: _categorySalesFuture,
            builder: (context, snapshot) {
              final items = snapshot.data ?? [];
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        strings.of('salesByCategory'),
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 8),
                      if (items.isEmpty)
                        Text(strings.of('noOrders'))
                      else
                        for (final item in items)
                          ListTile(
                            dense: true,
                            contentPadding: EdgeInsets.zero,
                            title: Text(item.categoryName),
                            trailing: Text(
                              formatCents(centsFromApi(item.totalRevenue)),
                            ),
                          ),
                    ],
                  ),
                ),
              );
            },
          ),
          const SizedBox(height: 16),
          FutureBuilder<DailyCloseTotals>(
            future: _dailyCloseFuture,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const SizedBox.shrink();
              }
              final t = snapshot.data;
              if (t == null) return const SizedBox.shrink();
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        strings.of('todayClose'),
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 12),
                      _metric(
                        context,
                        strings.of('grossRevenue'),
                        formatCents(centsFromApi(t.grossSalesTotal)),
                      ),
                      _metric(
                        context,
                        strings.of('netRevenue'),
                        formatCents(centsFromApi(t.netSalesTotal)),
                      ),
                      _metric(
                        context,
                        strings.of('cashSales'),
                        formatCents(centsFromApi(t.cashSalesTotal)),
                      ),
                      _metric(
                        context,
                        strings.of('refunds'),
                        formatCents(centsFromApi(t.refundsTotal)),
                      ),
                      _metric(
                        context,
                        strings.of('orders'),
                        '${t.completedOrderCount}',
                      ),
                      _metric(
                        context,
                        strings.of('shiftCount', args: {'count': t.shiftCount}),
                        '',
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
          const SizedBox(height: 16),
          FutureBuilder<List<Product>>(
            future: _lowStockFuture,
            builder: (context, snapshot) {
              final products = snapshot.data ?? [];
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        'Low stock',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 8),
                      if (products.isEmpty)
                        Text(strings.of('healthyStock'))
                      else
                        for (final product in products)
                          ListTile(
                            dense: true,
                            contentPadding: EdgeInsets.zero,
                            title: Text(product.name),
                            subtitle: Text(
                              '${product.stockQuantity} in stock · '
                              'reorder at ${product.reorderPoint}',
                            ),
                            trailing: Text(formatCents(product.priceCents)),
                          ),
                    ],
                  ),
                ),
              );
            },
          ),
          const SizedBox(height: 16),
          FutureBuilder<List<DailyShiftItem>>(
            future: _shiftsFuture,
            builder: (context, snapshot) {
              final shifts = snapshot.data ?? [];
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        strings.of('shifts'),
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 8),
                      if (shifts.isEmpty)
                        Text(strings.of('noOrders'))
                      else
                        for (final shift in shifts)
                          ListTile(
                            dense: true,
                            contentPadding: EdgeInsets.zero,
                            title: Text(
                              '${strings.of('shifts')} #'
                              '${shift.reconciliationId} — '
                              '${shift.operatorName ?? '-'}',
                            ),
                            subtitle: Text(formatDateTimeIso(shift.closedAt)),
                            trailing: Text(
                              formatCents(centsFromApi(shift.netSalesTotal)),
                            ),
                            onTap: () => _showShiftReport(shift),
                          ),
                    ],
                  ),
                ),
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _metric(BuildContext context, String label, String value) {
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
}
