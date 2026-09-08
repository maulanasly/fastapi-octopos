/// Branded skeletons — market teal placeholders.
library;

import 'package:flutter/material.dart';

import 'layout.dart';

/// Shimmer base — animated gradient between surfaceContainerHigh and
/// surfaceContainerHighest, no extra dep (pure LinearGradient + Animation).
class _Shimmer extends StatefulWidget {
  const _Shimmer({required this.child});

  final Widget child;

  @override
  State<_Shimmer> createState() => _ShimmerState();
}

class _ShimmerState extends State<_Shimmer> with SingleTickerProviderStateMixin {
  late final AnimationController _c;

  @override
  void initState() {
    super.initState();
    _c = AnimationController(vsync: this, duration: const Duration(milliseconds: 1200))..repeat();
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return AnimatedBuilder(
      animation: _c,
      builder: (context, child) {
        return ShaderMask(
          shaderCallback: (rect) {
            final t = _c.value;
            return LinearGradient(
              begin: Alignment(-1.0 + 2 * t, -0.3),
              end: Alignment(0.0 + 2 * t, 0.3),
              colors: [
                scheme.surfaceContainerHighest,
                scheme.surfaceContainerHigh,
                scheme.surfaceContainerHighest,
              ],
              stops: const [0.25, 0.5, 0.75],
            ).createShader(rect);
          },
          blendMode: BlendMode.srcATop,
          child: child,
        );
      },
      child: widget.child,
    );
  }
}

class _Box extends StatelessWidget {
  const _Box({this.width, this.height = 12, this.radius = 8});
  final double? width;
  final double height;
  final double radius;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(radius),
      ),
    );
  }
}

/// 4px teal accent strip skeleton
class _Strip extends StatelessWidget {
  const _Strip();
  @override
  Widget build(BuildContext context) {
    return Container(
      height: 4,
      color: Theme.of(context).colorScheme.outlineVariant.withValues(alpha: 0.35),
    );
  }
}

/// POS catalog grid skeleton — 6 tiles, category strip + image + bar
class ProductGridSkeleton extends StatelessWidget {
  const ProductGridSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return _Shimmer(
      child: GridView.builder(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(AppSpacing.sm),
        gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
          maxCrossAxisExtent: 200,
          childAspectRatio: 0.9,
          mainAxisSpacing: 8,
          crossAxisSpacing: 8,
        ),
        itemCount: 6,
        itemBuilder: (context, _) => Card(
          clipBehavior: Clip.antiAlias,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const _Strip(),
              Expanded(child: Container(color: Theme.of(context).colorScheme.surfaceContainerHigh)),
              Container(
                padding: const EdgeInsets.fromLTRB(AppSpacing.sm, AppSpacing.sm, AppSpacing.sm, 10),
                color: Theme.of(context).colorScheme.surfaceContainerLow,
                child: const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _Box(width: 120, height: 12),
                    SizedBox(height: 6),
                    _Box(width: 72, height: 14),
                    SizedBox(height: 6),
                    _Box(width: 80, height: 10),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Orders / inventory row skeleton — Card ListTile mimic
class OrderRowSkeleton extends StatelessWidget {
  const OrderRowSkeleton({super.key, this.count = 5});
  final int count;

  @override
  Widget build(BuildContext context) {
    return _Shimmer(
      child: ListView.separated(
        physics: const NeverScrollableScrollPhysics(),
        padding: const EdgeInsets.all(AppSpacing.lg),
        itemCount: count,
        separatorBuilder: (_, _) => const Divider(height: AppSpacing.sm),
        itemBuilder: (context, i) => Card(
          margin: EdgeInsets.zero,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Row(
              children: [
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _Box(width: 140, height: 14),
                      SizedBox(height: 8),
                      _Box(width: 200, height: 10),
                    ],
                  ),
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    _Box(width: 64, height: 20, radius: 999),
                    const SizedBox(height: 6),
                    _Box(width: 48, height: 10),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// KPI skeleton for reports/dashboard — 4 cards
class KpiSkeleton extends StatelessWidget {
  const KpiSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return _Shimmer(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
          children: List.generate(
            3,
            (_) => Card(
              margin: const EdgeInsets.only(bottom: AppSpacing.md),
              child: Padding(
                padding: const EdgeInsets.all(AppSpacing.lg),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _Box(width: 120, height: 12),
                    const SizedBox(height: 12),
                    _Box(width: 80, height: 20),
                    const SizedBox(height: 12),
                    _Box(width: double.infinity, height: 8),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Cart line skeleton — for checkout/cart pane
class CartLineSkeleton extends StatelessWidget {
  const CartLineSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return _Shimmer(
      child: ListView.separated(
        physics: const NeverScrollableScrollPhysics(),
        padding: const EdgeInsets.symmetric(horizontal: 12),
        itemCount: 3,
        separatorBuilder: (_, _) => const Divider(height: AppSpacing.sm),
        itemBuilder: (context, _) => Padding(
          padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
          child: Row(
            children: [
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _Box(width: 120, height: 12),
                    SizedBox(height: 6),
                    _Box(width: 80, height: 10),
                  ],
                ),
              ),
              _Box(width: 72, height: 10),
            ],
          ),
        ),
      ),
    );
  }
}
