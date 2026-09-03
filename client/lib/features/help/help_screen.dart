library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/strings.dart';

class HelpScreen extends ConsumerWidget {
  const HelpScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    return Scaffold(
      appBar: AppBar(title: Text(s.of('help'))),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(
            s.of('helpDescription'),
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 16),
          _HelpStep(
            icon: Icons.lock_open,
            title: s.of('helpStepDrawer'),
            subtitle: 'Open drawer → enter starting cash → Checkout unlocks',
          ),
          _HelpStep(
            icon: Icons.point_of_sale,
            title: s.of('helpStepCatalog'),
            subtitle: 'Scan barcode + Enter or tap a product tile',
          ),
          _HelpStep(
            icon: Icons.shopping_cart,
            title: s.of('helpStepCart'),
            subtitle: 'Cart survives refresh; use Guest or F3 for customers',
          ),
          _HelpStep(
            icon: Icons.payments,
            title: s.of('helpStepCheckout'),
            subtitle: 'F2 = Checkout, choose Cash / Card / Split, then Pay',
          ),
          _HelpStep(
            icon: Icons.people,
            title: s.of('helpStepCustomers'),
            subtitle: 'F3 = select customer, or create one in Customers tab',
          ),
          const Divider(height: 32),
          Text(
            'Tips',
            style: Theme.of(context).textTheme.titleSmall,
          ),
          const SizedBox(height: 8),
          const Text('• Offline: cached catalog still works, orders queue and sync when online.'),
          const Text('• Refunds: POS → Refunds (requires permission).'),
          const Text('• Reports/Settings: ask manager for access.'),
        ],
      ),
    );
  }
}

class _HelpStep extends StatelessWidget {
  const _HelpStep({required this.icon, required this.title, required this.subtitle});

  final IconData icon;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 28, color: Theme.of(context).colorScheme.primary),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: Theme.of(context).textTheme.titleSmall),
                const SizedBox(height: 4),
                Text(subtitle, style: Theme.of(context).textTheme.bodySmall),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
