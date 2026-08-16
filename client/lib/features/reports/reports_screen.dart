/// Reports screen: sales summary + low stock + shift reports.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/money.dart';
import '../../core/models.dart';

class ReportsScreen extends ConsumerStatefulWidget {
  const ReportsScreen({super.key});

  @override
  ConsumerState<ReportsScreen> createState() => _ReportsScreenState();
}

class _ReportsScreenState extends ConsumerState<ReportsScreen> {
  late Future<SalesSummary> _salesFuture;
  late Future<List<Product>> _lowStockFuture;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    _salesFuture = ref.read(reportRepositoryProvider).sales();
    _lowStockFuture = ref.read(reportRepositoryProvider).lowStock();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Reports'),
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
                      _metric(context, 'Orders', '${s.orderCount}'),
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
                        const Text('All product stock levels are healthy.')
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
