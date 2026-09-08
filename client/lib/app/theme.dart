/// OctoPOS brand theme — "Market Teal" palette.
///
/// Teal communicates trust and commerce (and the POS convention of
/// "green = settled"), sky secondary ties to the admin dashboard blue,
/// amber is reserved for money/promotions so pricing stays readable ink.
/// Light is the default mode; dark is fully supported and switchable.
library;

import 'package:flutter/material.dart';

/// Brand color tokens (both modes).
abstract final class AppColors {
  // Primary — teal
  static const Color primaryLight = Color(0xFF0F766E);
  static const Color primaryDark = Color(0xFF5EEAD4);
  static const Color onPrimaryLight = Color(0xFFFFFFFF);
  static const Color onPrimaryDark = Color(0xFF042F2E);
  static const Color primaryContainerLight = Color(0xFFCCFBF1);
  static const Color primaryContainerDark = Color(0xFF115E59);

  // Secondary — sky (ties to the admin dashboard blue)
  static const Color secondaryLight = Color(0xFF0284C7);
  static const Color secondaryDark = Color(0xFF7DD3FC);
  static const Color onSecondaryLight = Color(0xFFFFFFFF);
  static const Color onSecondaryDark = Color(0xFF082F49);
  static const Color secondaryContainerLight = Color(0xFFE0F2FE);
  static const Color secondaryContainerDark = Color(0xFF075985);

  // Tertiary / cash accent — amber (promotions, points, highlights)
  static const Color tertiaryLight = Color(0xFFB45309);
  static const Color tertiaryDark = Color(0xFFFCD34D);
  static const Color onTertiaryLight = Color(0xFFFFFFFF);
  static const Color onTertiaryDark = Color(0xFF451A03);
  static const Color tertiaryContainerLight = Color(0xFFFEF3C7);
  static const Color tertiaryContainerDark = Color(0xFF92400E);

  // Semantic
  static const Color success = Color(0xFF16A34A);
  static const Color successDark = Color(0xFF4ADE80);
  static const Color error = Color(0xFFDC2626);
  static const Color errorDark = Color(0xFFF87171);
  static const Color warning = Color(0xFFF59E0B);
  static const Color warningDark = Color(0xFFFBBF24);

  // Surfaces — warm-tinted neutrals
  static const Color surfaceLight = Color(0xFFF8FAF9);
  static const Color surfaceDark = Color(0xFF111418);
  static const Color surfaceContainerLight = Color(0xFFFFFFFF);
  static const Color surfaceContainerDark = Color(0xFF1A1F1E);
  static const Color surfaceContainerHighLight = Color(0xFFEFF1F0);
  static const Color surfaceContainerHighDark = Color(0xFF242A29);

  // Ink
  static const Color onSurfaceLight = Color(0xFF1A2321);
  static const Color onSurfaceDark = Color(0xFFE3E7E5);
  static const Color outlineLight = Color(0xFFB3B9B7);
  static const Color outlineDark = Color(0xFF4A5451);

  // Brand accents
  static const LinearGradient brandGradientLight = LinearGradient(
    colors: [Color(0xFF0F766E), Color(0xFF0D9488)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
  static const LinearGradient brandGradientDark = LinearGradient(
    colors: [Color(0xFF115E59), Color(0xFF0F766E)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
}

/// Centralized theme config. Light is the default mode.
abstract final class AppTheme {
  static const ThemeMode defaultThemeMode = ThemeMode.light;

  static ThemeData get light => _build(Brightness.light);
  static ThemeData get dark => _build(Brightness.dark);

  static ThemeData _build(Brightness brightness) {
    final isDark = brightness == Brightness.dark;
    final scheme = ColorScheme(
      brightness: brightness,
      primary: isDark ? AppColors.primaryDark : AppColors.primaryLight,
      onPrimary: isDark ? AppColors.onPrimaryDark : AppColors.onPrimaryLight,
      primaryContainer: isDark
          ? AppColors.primaryContainerDark
          : AppColors.primaryContainerLight,
      onPrimaryContainer: isDark
          ? AppColors.onPrimaryDark
          : AppColors.onPrimaryLight,
      secondary: isDark ? AppColors.secondaryDark : AppColors.secondaryLight,
      onSecondary: isDark
          ? AppColors.onSecondaryDark
          : AppColors.onSecondaryLight,
      secondaryContainer: isDark
          ? AppColors.secondaryContainerDark
          : AppColors.secondaryContainerLight,
      onSecondaryContainer: isDark
          ? AppColors.onSecondaryDark
          : AppColors.onSecondaryLight,
      tertiary: isDark ? AppColors.tertiaryDark : AppColors.tertiaryLight,
      onTertiary: isDark ? AppColors.onTertiaryDark : AppColors.onTertiaryLight,
      tertiaryContainer: isDark
          ? AppColors.tertiaryContainerDark
          : AppColors.tertiaryContainerLight,
      onTertiaryContainer: isDark
          ? AppColors.onTertiaryDark
          : AppColors.onTertiaryLight,
      error: isDark ? AppColors.errorDark : AppColors.error,
      onError: Colors.white,
      errorContainer: isDark
          ? const Color(0xFF7F1D1D)
          : const Color(0xFFFEE2E2),
      onErrorContainer: isDark
          ? const Color(0xFFFECACA)
          : const Color(0xFF7F1D1D),
      surface: isDark ? AppColors.surfaceDark : AppColors.surfaceLight,
      onSurface: isDark ? AppColors.onSurfaceDark : AppColors.onSurfaceLight,
      surfaceContainerLowest: isDark
          ? const Color(0xFF0C0F12)
          : const Color(0xFFFFFFFF),
      surfaceContainerLow: isDark
          ? AppColors.surfaceContainerDark
          : AppColors.surfaceContainerLight,
      surfaceContainer: isDark
          ? AppColors.surfaceContainerDark
          : AppColors.surfaceContainerLight,
      surfaceContainerHigh: isDark
          ? AppColors.surfaceContainerHighDark
          : AppColors.surfaceContainerHighLight,
      surfaceContainerHighest: isDark
          ? AppColors.surfaceContainerHighDark
          : AppColors.surfaceContainerHighLight,
      onSurfaceVariant: isDark
          ? const Color(0xFFC2C9C7)
          : const Color(0xFF4B5552),
      outline: isDark ? AppColors.outlineDark : AppColors.outlineLight,
      outlineVariant: isDark
          ? const Color(0xFF3A4341)
          : const Color(0xFFDDE3E1),
      shadow: Colors.black,
      scrim: Colors.black,
      inverseSurface: isDark
          ? AppColors.onSurfaceDark
          : AppColors.onSurfaceLight,
      onInverseSurface: isDark ? AppColors.surfaceDark : AppColors.surfaceLight,
      inversePrimary: isDark ? AppColors.primaryLight : AppColors.primaryDark,
    );

    final base = ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: scheme.surface,
    );

    return base.copyWith(
      appBarTheme: AppBarTheme(
        backgroundColor: scheme.surface,
        foregroundColor: scheme.onSurface,
        elevation: 0,
        scrolledUnderElevation: 1,
        surfaceTintColor: Colors.transparent,
      ),
      navigationRailTheme: NavigationRailThemeData(
        backgroundColor: scheme.surface,
        indicatorColor: scheme.primaryContainer,
        selectedIconTheme: IconThemeData(color: scheme.primary),
        selectedLabelTextStyle: TextStyle(
          color: scheme.primary,
          fontWeight: FontWeight.w600,
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size(0, 44),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          textStyle: const TextStyle(fontWeight: FontWeight.w600),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size(0, 44),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
        isDense: true,
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        color: scheme.surfaceContainerLow,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: BorderSide(color: scheme.outlineVariant),
        ),
      ),
      chipTheme: ChipThemeData(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        side: BorderSide(color: scheme.outlineVariant),
      ),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
      segmentedButtonTheme: SegmentedButtonThemeData(
        style: ButtonStyle(
          side: WidgetStatePropertyAll(
            BorderSide(color: scheme.outlineVariant),
          ),
        ),
      ),
    );
  }
}
