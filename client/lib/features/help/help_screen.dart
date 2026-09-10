library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/app_icons.dart';
import '../../core/layout.dart';
import '../../core/strings.dart';

class HelpScreen extends ConsumerWidget {
  const HelpScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    return Scaffold(
      appBar: AppBar(title: Text(s.of('help'))),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.lg),
        children: [
          Text(
            s.of('helpDescription'),
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: AppSpacing.lg),
          _HelpStep(
            icon: AppIcons.drawerOpen,
            title: s.of('helpStepDrawer'),
            subtitle: s.of('helpStepDrawerHint'),
          ),
          _HelpStep(
            icon: AppIcons.pos,
            title: s.of('helpStepCatalog'),
            subtitle: s.of('helpStepCatalogHint'),
          ),
          _HelpStep(
            icon: AppIcons.shoppingCart,
            title: s.of('helpStepCart'),
            subtitle: s.of('helpStepCartHint'),
          ),
          _HelpStep(
            icon: AppIcons.payments,
            title: s.of('helpStepCheckout'),
            subtitle: s.of('helpStepCheckoutHint'),
          ),
          _HelpStep(
            icon: AppIcons.customers,
            title: s.of('helpStepCustomers'),
            subtitle: s.of('helpStepCustomersHint'),
          ),
          const Divider(height: 32),
          Text(
            s.of('tipsTitle'),
            style: Theme.of(context).textTheme.titleSmall,
          ),
          const SizedBox(height: AppSpacing.sm),
          Text(s.of('tipsOffline')),
          Text(s.of('tipsRefunds')),
          Text(s.of('tipsReports')),
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
      padding: const EdgeInsets.only(bottom: AppSpacing.lg),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 28, color: Theme.of(context).colorScheme.primary),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: Theme.of(context).textTheme.titleSmall),
                const SizedBox(height: AppSpacing.xs),
                Text(subtitle, style: Theme.of(context).textTheme.bodySmall),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
