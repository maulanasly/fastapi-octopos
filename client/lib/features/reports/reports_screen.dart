/// Reports screen: sales summary, daily close, low stock, shift reports.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/async_views.dart';
import '../../core/dates.dart';
import '../../core/layout.dart';
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
  late Future<SupplierSpendSummary> _supplierSpendFuture;
  late Future<VarianceTrendSummary> _varianceTrendFuture;

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
    _supplierSpendFuture = repo.supplierSpend(
      startDate: startDate,
      endDate: endDate,
    );
    _varianceTrendFuture = repo.purchaseVariance(
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
        padding: const EdgeInsets.all(AppSpacing.lg),
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
          const SizedBox(height: AppSpacing.lg),
          FutureBuilder<SalesSummary>(
            future: _salesFuture,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const Padding(
                  padding: EdgeInsets.all(AppSpacing.xxl),
                  child: LoadingStateView(),
                );
              }
              if (snapshot.hasError) {
                return ErrorStateView(
                  message: strings.of('genericError'),
                  onRetry: () => setState(_load),
                );
              }
              final s = snapshot.data!;
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.lg),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        strings.of('salesSummary'),
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: AppSpacing.md),
                      _metric(
                        context,
                        strings.of('grossRevenue'),
                        formatCents(centsFromApi(s.grossRevenue)),
                      ),
                      _metric(
                        context,
                        strings.of('discounts'),
                        formatCents(centsFromApi(s.totalDiscounts)),
                      ),
                      _metric(
                        context,
                        strings.of('refunds'),
                        formatCents(centsFromApi(s.totalRefunds)),
                      ),
                      _metric(
                        context,
                        strings.of('netRevenue'),
                        formatCents(centsFromApi(s.netRevenue)),
                      ),
                      _metric(context, strings.of('orders'), '${s.orderCount}'),
                      _metric(
                        context,
                        strings.of('avgOrder'),
                        formatCents(centsFromApi(s.averageOrderValue)),
                      ),
                      _metric(
                        context,
                        strings.of('cogsTotal'),
                        formatCents(centsFromApi(s.cogsTotal)),
                      ),
                      _metric(
                        context,
                        strings.of('grossMargin'),
                        s.grossMarginPercent == null
                            ? '—'
                            : '${formatCents(centsFromApi(s.grossMarginAmount))} '
                                '(${s.grossMarginPercent!.toStringAsFixed(1)}%)',
                      ),
                      if (s.cogsKnownRatio != null && s.cogsKnownRatio! < 1)
                        Padding(
                          padding: const EdgeInsets.only(top: AppSpacing.xs),
                          child: Text(
                            strings.of('partialCostData'),
                            style: Theme.of(context).textTheme.bodySmall
                                ?.copyWith(
                                  color: Theme.of(
                                    context,
                                  ).colorScheme.onSurfaceVariant,
                                ),
                          ),
                        ),
                    ],
                  ),
                ),
              );
            },
          ),
          const SizedBox(height: AppSpacing.lg),
          FutureBuilder<List<TopProductItem>>(
            future: _topProductsFuture,
            builder: (context, snapshot) {
              final items = snapshot.data ?? [];
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.lg),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        strings.of('topProducts'),
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: AppSpacing.sm),
                      if (items.isEmpty)
                        Text(strings.of('noOrders'))
                      else
                        for (final item in items)
                          _ReportRow(
                            title: item.productName,
                            subtitle:
                                '${item.totalQuantitySold} × ${item.productSku}',
                            amount: formatCents(
                              centsFromApi(item.totalRevenue),
                            ),
                          ),
                    ],
                  ),
                ),
              );
            },
          ),
          const SizedBox(height: AppSpacing.lg),
          FutureBuilder<List<CategorySalesItem>>(
            future: _categorySalesFuture,
            builder: (context, snapshot) {
              final items = snapshot.data ?? [];
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.lg),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        strings.of('salesByCategory'),
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: AppSpacing.sm),
                      if (items.isEmpty)
                        Text(strings.of('noOrders'))
                      else
                        for (final item in items)
                          _ReportRow(
                            title: item.categoryName,
                            amount: formatCents(
                              centsFromApi(item.totalRevenue),
                            ),
                          ),
                    ],
                  ),
                ),
              );
            },
          ),
          const SizedBox(height: AppSpacing.lg),
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
                  padding: const EdgeInsets.all(AppSpacing.lg),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        strings.of('todayClose'),
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: AppSpacing.md),
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
          const SizedBox(height: AppSpacing.lg),
          FutureBuilder<List<Product>>(
            future: _lowStockFuture,
            builder: (context, snapshot) {
              final products = snapshot.data ?? [];
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.lg),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        strings.of('lowStock'),
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: AppSpacing.sm),
                      if (products.isEmpty)
                        Text(strings.of('healthyStock'))
                      else
                        for (final product in products)
                          _ReportRow(
                            title: product.name,
                            subtitle:
                                '${product.stockQuantity} in stock · '
                                'reorder at ${product.reorderPoint}',
                            amount: formatCents(product.priceCents),
                          ),
                    ],
                  ),
                ),
              );
            },
          ),
          const SizedBox(height: AppSpacing.lg),
          FutureBuilder<List<DailyShiftItem>>(
            future: _shiftsFuture,
            builder: (context, snapshot) {
              final shifts = snapshot.data ?? [];
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.lg),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        strings.of('shifts'),
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: AppSpacing.sm),
                      if (shifts.isEmpty)
                        Text(strings.of('noOrders'))
                      else
                        for (final shift in shifts)
                          _ReportRow(
                            title:
                                '${strings.of('shifts')} #'
                                '${shift.reconciliationId} — '
                                '${shift.operatorName ?? '-'}',
                            subtitle: formatDateTimeIso(shift.closedAt),
                            amount: formatCents(
                              centsFromApi(shift.netSalesTotal),
                            ),
                            onTap: () => _showShiftReport(shift),
                          ),
                    ],
                  ),
                ),
              );
            },
          ),
          const SizedBox(height: AppSpacing.lg),
          FutureBuilder<SupplierSpendSummary>(
            future: _supplierSpendFuture,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const Padding(
                  padding: EdgeInsets.all(AppSpacing.xxl),
                  child: LoadingStateView(),
                );
              }
              if (snapshot.hasError) {
                return ErrorStateView(
                  message: strings.of('genericError'),
                  onRetry: () => setState(_load),
                );
              }
              final spend = snapshot.data!;
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.lg),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        strings.of('supplierSpend'),
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: AppSpacing.md),
                      _metric(
                        context,
                        strings.of('cogsEstimate'),
                        formatCents(centsFromApi(spend.cogsEstimate)),
                      ),
                      const SizedBox(height: AppSpacing.sm),
                      if (spend.items.isEmpty)
                        Text(strings.of('noInvoices'))
                      else
                        for (final item in spend.items)
                          _ReportRow(
                            title: item.supplierName,
                            subtitle:
                                '${item.poCount} PO · ${item.invoiceCount} inv',
                            amount:
                                '${formatCents(centsFromApi(item.approvedTotal))}'
                                '${item.varianceTotal != 0 ? ' (±${formatCents(centsFromApi(item.varianceTotal.abs()))})' : ''}',
                          ),
                    ],
                  ),
                ),
              );
            },
          ),
          const SizedBox(height: AppSpacing.lg),
          FutureBuilder<VarianceTrendSummary>(
            future: _varianceTrendFuture,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const Padding(
                  padding: EdgeInsets.all(AppSpacing.xxl),
                  child: LoadingStateView(),
                );
              }
              if (snapshot.hasError) {
                return ErrorStateView(
                  message: strings.of('genericError'),
                  onRetry: () => setState(_load),
                );
              }
              final trend = snapshot.data!;
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.lg),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        strings.of('purchaseVarianceTrend'),
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: AppSpacing.sm),
                      if (trend.months.isEmpty)
                        Text(strings.of('noInvoices'))
                      else
                        for (final month in trend.months)
                          _ReportRow(
                            title: month.period,
                            subtitle:
                                '${month.invoiceCount} inv · '
                                'approved ${formatCents(centsFromApi(month.approvedTotal))}',
                            amount:
                                '±${formatCents(centsFromApi(month.varianceTotal.abs()))}',
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

/// Branded ledger row — title + subtitle left, tabular amount right.
/// Replaces stock `ListTile` so report sections read as ERP, not demo.
class _ReportRow extends StatelessWidget {
  const _ReportRow({
    required this.title,
    this.subtitle,
    required this.amount,
    this.onTap,
  });

  final String title;
  final String? subtitle;
  final String amount;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(AppRadius.sm),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: AppSpacing.xs),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: Theme.of(context).textTheme.titleSmall,
                  ),
                  if (subtitle != null)
                    Text(
                      subtitle!,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: scheme.onSurfaceVariant,
                          ),
                    ),
                ],
              ),
            ),
            const SizedBox(width: AppSpacing.md),
            Text(
              amount,
              textAlign: TextAlign.right,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                    fontFeatures: const [FontFeature.tabularFigures()],
                    color: scheme.onSurface,
                  ),
            ),
          ],
        ),
      ),
    );
  }
}
