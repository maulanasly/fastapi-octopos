/// Category color helpers: hex parsing and contrast-aware text colors.
library;

import 'package:flutter/material.dart';

/// Parses a `#RRGGBB` hex string; null for anything invalid.
Color? colorFromHex(String? hex) {
  if (hex == null || hex.isEmpty) return null;
  final cleaned = hex.replaceFirst('#', '');
  if (cleaned.length != 6) return null;
  final value = int.tryParse(cleaned, radix: 16);
  if (value == null) return null;
  return Color(0xFF000000 | value);
}

/// Readable text color for a given background (black on light, white on dark).
Color textColorOn(Color background) {
  // Relative luminance per WCAG; > 0.5 is light.
  final luminance = background.computeLuminance();
  return luminance > 0.5 ? Colors.black87 : Colors.white;
}

/// Category accent color with a soft tint for chip backgrounds.
Color softBackground(Color color, {double alpha = 0.15}) =>
    color.withValues(alpha: alpha);
