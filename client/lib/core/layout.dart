/// Shared responsive layout helpers + design tokens.
library;

import 'package:flutter/material.dart';

/// Spacing scale — 4pt base. Use instead of raw `8`/`16` literals.
abstract final class AppSpacing {
  static const double xs = 4;
  static const double sm = 8;
  static const double md = 12;
  static const double lg = 16;
  static const double xl = 24;
  static const double xxl = 32;
  static const double xxxl = 48;
}

/// Corner radii — aligns with `AppTheme` component radii.
abstract final class AppRadius {
  static const double sm = 8;
  static const double md = 12;
  static const double lg = 14;
  static const double xl = 16;
  static const double xxl = 20;
  static const double sheet = 24;
  static const double pill = 999;
}

/// Breakpoints — M3 window size classes.
/// compact < 600, medium 600–840, expanded 840–1200, large 1200+.
abstract final class AppBreakpoints {
  static const double compact = 600;
  static const double medium = 840;
  static const double expanded = 1200;
  static const double dialogMax = 420;
  static const double dialogMedium = 560;
  static const double dialogSmall = 360;
  static const double dialogXLarge = 640;

  static bool isCompact(BuildContext context) =>
      MediaQuery.sizeOf(context).width < medium;
  static bool isMedium(BuildContext context) {
    final w = MediaQuery.sizeOf(context).width;
    return w >= medium && w < expanded;
  }

  static bool isExpanded(BuildContext context) =>
      MediaQuery.sizeOf(context).width >= expanded;
}

/// Elevation tokens — mirrors `AppTheme` elevation.
abstract final class AppElevation {
  static const double none = 0;
  static const double card = 1;
  static const double raised = 3;
  static const double snackbar = 4;
  static const double bottomSheet = 8;
  static const double dialog = 8;
}

/// Dialog width that fits the screen (phones) while staying readable on
/// larger displays.
double dialogWidth(BuildContext context) {
  return (MediaQuery.sizeOf(context).width - 32).clamp(0.0, AppBreakpoints.dialogMax);
}

/// Dialog width variants — use instead of magic `360`/`400`/`480`.
double dialogWidthSmall(BuildContext context) {
  return (MediaQuery.sizeOf(context).width - 32).clamp(0.0, AppBreakpoints.dialogSmall);
}

double dialogWidthLarge(BuildContext context) {
  return (MediaQuery.sizeOf(context).width - 32).clamp(0.0, AppBreakpoints.dialogMedium);
}

/// Extra-large dialog/page cap (e.g. two-pane refund flow) — clamps
/// phones, keeps the 640 desktop width.
double dialogWidthXLarge(BuildContext context) {
  return (MediaQuery.sizeOf(context).width - 32).clamp(0.0, AppBreakpoints.dialogXLarge);
}
