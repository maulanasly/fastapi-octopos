/// POS product tile: category accent strip, image (or monogram), and a
/// fixed bottom label bar so the name is always visible and tile heights
/// stay uniform.
library;

import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/colors.dart';
import '../../core/config.dart';
import '../../core/models.dart';
import '../../core/money.dart';
import '../../core/strings.dart';

class ProductTile extends ConsumerWidget {
  const ProductTile({super.key, required this.product, this.onTap});

  final Product product;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    final outOfStock = product.stockQuantity <= 0;
    final categoryColor = colorFromHex(product.category?.color);
    final barColor = categoryColor != null
        ? softBackground(categoryColor)
        : Theme.of(context).colorScheme.surfaceContainerLow;
    final nameColor = categoryColor != null
        ? textColorOn(barColor)
        : Theme.of(context).colorScheme.onSurface;

    return Card(
      clipBehavior: Clip.antiAlias,
      color: outOfStock
          ? Theme.of(context).colorScheme.surfaceContainerHighest
          : null,
      child: InkWell(
        onTap: outOfStock ? null : onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              height: 4,
              color:
                  categoryColor ??
                  (outOfStock
                      ? Theme.of(context).colorScheme.surfaceContainerHighest
                      : Theme.of(context).colorScheme.outlineVariant),
            ),
            // Flexible image: fills whatever remains above the fixed bar,
            // so the tile never overflows no matter the label length.
            // Thumbnail is preferred for grid payloads; falls back to the
            // full image, then to a monogram, and is cached on device.
            Expanded(
              child: _ProductImage(product: product),
            ),
            // Fixed bottom label bar: product name always visible.
            Container(
              padding: const EdgeInsets.fromLTRB(8, 8, 8, 10),
              color: barColor,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    product.name,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(
                      context,
                    ).textTheme.titleSmall?.copyWith(color: nameColor),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    formatCents(product.priceCents),
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: Theme.of(context).colorScheme.primary,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Text(
                    s.of('inStock', args: {'count': product.stockQuantity}),
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: outOfStock
                          ? Theme.of(context).colorScheme.error
                          : Colors.grey,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Cached product image (thumbnail preferred) with monogram fallbacks.
class _ProductImage extends StatelessWidget {
  const _ProductImage({required this.product});

  final Product product;

  @override
  Widget build(BuildContext context) {
    final url = product.thumbnailUrl ?? product.imageUrl;
    if (url == null) return _ProductMonogram(product: product);
    return CachedNetworkImage(
      imageUrl: '${AppConfig.mediaBaseUrl}$url',
      fit: BoxFit.cover,
      errorWidget: (_, _, _) => _ProductMonogram(product: product),
      placeholder: (_, _) => _ProductMonogram(product: product, showIcon: true),
    );
  }
}

/// Monogram fallback (category-colored) for products without an image.
class _ProductMonogram extends StatelessWidget {
  const _ProductMonogram({required this.product, this.showIcon = false});

  final Product product;
  final bool showIcon;

  @override
  Widget build(BuildContext context) {
    final color =
        colorFromHex(product.category?.color) ??
        Theme.of(context).colorScheme.surfaceContainerHighest;
    return Container(
      color: color,
      alignment: Alignment.center,
      child: showIcon
          ? Icon(
              Icons.image_outlined,
              size: 32,
              color: textColorOn(color).withValues(alpha: 0.6),
            )
          : Text(
              product.name.isEmpty ? '?' : product.name[0].toUpperCase(),
              style: TextStyle(
                fontSize: 32,
                fontWeight: FontWeight.bold,
                color: textColorOn(color),
              ),
            ),
    );
  }
}
