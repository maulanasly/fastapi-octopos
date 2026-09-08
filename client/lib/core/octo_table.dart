/// Branded data table — Market Teal header, zebra, numeric alignment.
library;

import 'package:flutter/material.dart';

import 'layout.dart';

class OctoTableColumn {
  const OctoTableColumn(this.label, {this.numeric = false, this.flex = 1});

  final String label;
  final bool numeric;
  final int flex;
}

class OctoTable extends StatelessWidget {
  const OctoTable({
    super.key,
    required this.columns,
    required this.rows,
    this.onRowTap,
  });

  final List<OctoTableColumn> columns;
  final List<List<Widget>> rows;
  final void Function(int index)? onRowTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final headerStyle = Theme.of(context).textTheme.labelSmall?.copyWith(
          color: scheme.onSurfaceVariant,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.06 * 11,
        );
    return Card(
      margin: EdgeInsets.zero,
      clipBehavior: Clip.antiAlias,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Header
          Container(
            color: scheme.surfaceContainerHigh,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            child: Row(
              children: [
                for (final col in columns)
                  Expanded(
                    flex: col.flex,
                    child: Text(
                      col.label.toUpperCase(),
                      style: headerStyle,
                      textAlign: col.numeric ? TextAlign.right : TextAlign.left,
                    ),
                  ),
              ],
            ),
          ),
          const Divider(height: 1, thickness: 1),
          // Rows
          ...List.generate(rows.length, (i) {
            final cells = rows[i];
            final isOdd = i.isOdd;
            return InkWell(
              onTap: onRowTap == null ? null : () => onRowTap!(i),
              child: Container(
                color: isOdd ? scheme.surfaceContainerLow : scheme.surfaceContainerHighest.withValues(alpha: 0.5),
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                child: Row(
                  children: [
                    for (var c = 0; c < cells.length; c++)
                      Expanded(
                        flex: columns[c].flex,
                        child: Align(
                          alignment: columns[c].numeric ? Alignment.centerRight : Alignment.centerLeft,
                          child: DefaultTextStyle(
                            style: Theme.of(context).textTheme.bodyMedium!.copyWith(
                                  fontWeight: columns[c].numeric ? FontWeight.w600 : FontWeight.w400,
                                  fontFeatures: columns[c].numeric ? const [FontFeature.tabularFigures()] : null,
                                  color: columns[c].numeric ? scheme.onSurface : scheme.onSurface,
                                ),
                            child: cells[c],
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            );
          }),
        ],
      ),
    );
  }
}

/// Responsive wrapper — table on wide, cards on narrow.
class OctoResponsiveTable extends StatelessWidget {
  const OctoResponsiveTable({
    super.key,
    required this.columns,
    required this.rows,
    this.cardBuilder,
    this.onRowTap,
  });

  final List<OctoTableColumn> columns;
  final List<List<Widget>> rows;
  final Widget Function(BuildContext context, int index)? cardBuilder;
  final void Function(int index)? onRowTap;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final isNarrow = constraints.maxWidth < AppBreakpoints.compact;
        if (isNarrow && cardBuilder != null) {
          return ListView.separated(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(AppSpacing.lg),
            itemCount: rows.length,
            separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.sm),
            itemBuilder: (context, i) => cardBuilder!(context, i),
          );
        }
        return SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(AppSpacing.lg),
          child: OctoTable(columns: columns, rows: rows, onRowTap: onRowTap),
        );
      },
    );
  }
}
