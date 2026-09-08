/// OctoPOS brand theme — "Market Teal" palette.
///
/// Teal communicates trust and commerce (and the POS convention of
/// "green = settled"), sky secondary ties to the admin dashboard blue,
/// amber is reserved for money/promotions so pricing stays readable ink.
/// Light is the default mode; dark is fully supported and switchable.
library;

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

bool get _isTest {
  try {
    return WidgetsBinding.instance.runtimeType.toString().contains('Test');
  } catch (_) {
    return false;
  }
}

TextStyle _fontFamily(
  String family, {
  double? fontSize,
  FontWeight? fontWeight,
  double? letterSpacing,
  Color? color,
}) {
  if (_isTest) {
    return TextStyle(
      fontFamily: family,
      fontSize: fontSize,
      fontWeight: fontWeight,
      letterSpacing: letterSpacing,
      color: color,
    );
  }
  if (family == 'PlusJakartaSans') {
    return GoogleFonts.plusJakartaSans(
      fontSize: fontSize,
      fontWeight: fontWeight,
      letterSpacing: letterSpacing,
      color: color,
    );
  }
  return GoogleFonts.inter(
    fontSize: fontSize,
    fontWeight: fontWeight,
    letterSpacing: letterSpacing,
    color: color,
  );
}

TextStyle _plusJakartaSans({
  double? fontSize,
  FontWeight? fontWeight,
  double? letterSpacing,
  Color? color,
}) => _fontFamily('PlusJakartaSans', fontSize: fontSize, fontWeight: fontWeight, letterSpacing: letterSpacing, color: color);

TextStyle _inter({
  double? fontSize,
  FontWeight? fontWeight,
  double? letterSpacing,
  Color? color,
}) => _fontFamily('Inter', fontSize: fontSize, fontWeight: fontWeight, letterSpacing: letterSpacing, color: color);


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

  // Surfaces — warm-tinted neutrals (distinct levels for M3 elevation)
  static const Color surfaceLight = Color(0xFFF8FAF9);
  static const Color surfaceDark = Color(0xFF111418);
  static const Color surfaceContainerLowestLight = Color(0xFFFFFFFF);
  static const Color surfaceContainerLowestDark = Color(0xFF0C0F12);
  static const Color surfaceContainerLight = Color(0xFFFFFFFF);
  static const Color surfaceContainerDark = Color(0xFF1A1F1E);
  static const Color surfaceContainerHighLight = Color(0xFFEFF1F0);
  static const Color surfaceContainerHighDark = Color(0xFF242A29);
  static const Color surfaceContainerHighestLight = Color(0xFFE8EBEA);
  static const Color surfaceContainerHighestDark = Color(0xFF2C3331);

  // Ink
  static const Color onSurfaceLight = Color(0xFF1A2321);
  static const Color onSurfaceDark = Color(0xFFE3E7E5);
  static const Color outlineLight = Color(0xFFB3B9B7);
  static const Color outlineDark = Color(0xFF4A5451);

  // Error containers (tokenized, previously hard-coded in ColorScheme)
  static const Color errorContainerLight = Color(0xFFFEE2E2);
  static const Color errorContainerDark = Color(0xFF7F1D1D);
  static const Color onErrorContainerLight = Color(0xFF7F1D1D);
  static const Color onErrorContainerDark = Color(0xFFFECACA);

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
          ? AppColors.primaryContainerLight
          : AppColors.onPrimaryDark,
      secondary: isDark ? AppColors.secondaryDark : AppColors.secondaryLight,
      onSecondary: isDark
          ? AppColors.onSecondaryDark
          : AppColors.onSecondaryLight,
      secondaryContainer: isDark
          ? AppColors.secondaryContainerDark
          : AppColors.secondaryContainerLight,
      onSecondaryContainer: isDark
          ? AppColors.secondaryContainerLight
          : AppColors.onSecondaryDark,
      tertiary: isDark ? AppColors.tertiaryDark : AppColors.tertiaryLight,
      onTertiary: isDark ? AppColors.onTertiaryDark : AppColors.onTertiaryLight,
      tertiaryContainer: isDark
          ? AppColors.tertiaryContainerDark
          : AppColors.tertiaryContainerLight,
      onTertiaryContainer: isDark
          ? AppColors.tertiaryContainerLight
          : AppColors.onTertiaryDark,
      error: isDark ? AppColors.errorDark : AppColors.error,
      onError: Colors.white,
      errorContainer: isDark
          ? AppColors.errorContainerDark
          : AppColors.errorContainerLight,
      onErrorContainer: isDark
          ? AppColors.onErrorContainerDark
          : AppColors.onErrorContainerLight,
      surface: isDark ? AppColors.surfaceDark : AppColors.surfaceLight,
      onSurface: isDark ? AppColors.onSurfaceDark : AppColors.onSurfaceLight,
      surfaceContainerLowest: isDark
          ? AppColors.surfaceContainerLowestDark
          : AppColors.surfaceContainerLowestLight,
      surfaceContainerLow: isDark
          ? AppColors.surfaceContainerDark
          : AppColors.surfaceContainerLight,
      surfaceContainer: isDark
          ? AppColors.surfaceLight
          : AppColors.surfaceLight,
      surfaceContainerHigh: isDark
          ? AppColors.surfaceContainerHighDark
          : AppColors.surfaceContainerHighLight,
      surfaceContainerHighest: isDark
          ? AppColors.surfaceContainerHighestDark
          : AppColors.surfaceContainerHighestLight,
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

    final baseText = TextTheme(
      displayLarge: _plusJakartaSans(
        fontSize: 32, fontWeight: FontWeight.w800, letterSpacing: -0.02 * 32, color: scheme.onSurface),
      displayMedium: _plusJakartaSans(
        fontSize: 28, fontWeight: FontWeight.w800, letterSpacing: -0.02 * 28, color: scheme.onSurface),
      displaySmall: _plusJakartaSans(
        fontSize: 24, fontWeight: FontWeight.w700, letterSpacing: -0.01 * 24, color: scheme.onSurface),
      headlineLarge: _plusJakartaSans(
        fontSize: 22, fontWeight: FontWeight.w700, letterSpacing: -0.01 * 22, color: scheme.onSurface),
      headlineMedium: _plusJakartaSans(
        fontSize: 18, fontWeight: FontWeight.w700, letterSpacing: -0.01 * 18, color: scheme.onSurface),
      headlineSmall: _plusJakartaSans(
        fontSize: 16, fontWeight: FontWeight.w700, color: scheme.onSurface),
      titleLarge: _plusJakartaSans(
        fontSize: 22, fontWeight: FontWeight.w700, letterSpacing: -0.01 * 22, color: scheme.onSurface),
      titleMedium: _inter(
        fontSize: 16, fontWeight: FontWeight.w600, letterSpacing: -0.01 * 16, color: scheme.onSurface),
      titleSmall: _inter(
        fontSize: 14, fontWeight: FontWeight.w600, letterSpacing: 0.01 * 14, color: scheme.onSurface),
      bodyLarge: _inter(fontSize: 16, fontWeight: FontWeight.w400, color: scheme.onSurface),
      bodyMedium: _inter(fontSize: 14, fontWeight: FontWeight.w400, color: scheme.onSurface),
      bodySmall: _inter(
        fontSize: 12, fontWeight: FontWeight.w400, color: scheme.onSurfaceVariant),
      labelLarge: _inter(
        fontSize: 14, fontWeight: FontWeight.w600, letterSpacing: 0.02 * 14, color: scheme.onSurface),
      labelMedium: _inter(
        fontSize: 12, fontWeight: FontWeight.w600, letterSpacing: 0.02 * 12, color: scheme.onSurfaceVariant),
      labelSmall: _inter(
        fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 0.06 * 11, color: scheme.onSurfaceVariant),
    );

    final base = ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: scheme.surface,
      textTheme: baseText,
    );

    return base.copyWith(
      appBarTheme: AppBarTheme(
        backgroundColor: scheme.surfaceContainerLow.withValues(alpha: 0.8),
        foregroundColor: scheme.onSurface,
        elevation: 0,
        scrolledUnderElevation: 0,
        surfaceTintColor: Colors.transparent,
        centerTitle: false,
        titleTextStyle: _plusJakartaSans(
          fontSize: 18, fontWeight: FontWeight.w800, letterSpacing: -0.02 * 18, color: scheme.onSurface),
      ),
      navigationRailTheme: NavigationRailThemeData(
        backgroundColor: scheme.surfaceContainerLow,
        indicatorColor: scheme.primaryContainer,
        indicatorShape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        selectedIconTheme: IconThemeData(color: scheme.primary, size: 24),
        unselectedIconTheme: IconThemeData(color: scheme.onSurfaceVariant, size: 22),
        selectedLabelTextStyle: _inter(color: scheme.primary, fontWeight: FontWeight.w700, fontSize: 12),
        unselectedLabelTextStyle: _inter(color: scheme.onSurfaceVariant, fontWeight: FontWeight.w500, fontSize: 12),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: scheme.surfaceContainerLow,
        indicatorColor: scheme.primaryContainer,
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return _inter(color: scheme.primary, fontWeight: FontWeight.w700, fontSize: 12);
          }
          return _inter(color: scheme.onSurfaceVariant, fontWeight: FontWeight.w500, fontSize: 12);
        }),
        iconTheme: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) return IconThemeData(color: scheme.primary);
          return IconThemeData(color: scheme.onSurfaceVariant);
        }),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: scheme.primary,
          foregroundColor: scheme.onPrimary,
          minimumSize: const Size(0, 44),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          textStyle: _inter(fontWeight: FontWeight.w700, fontSize: 14, letterSpacing: 0.01 * 14),
          elevation: 0,
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: scheme.primary,
          minimumSize: const Size(0, 44),
          side: BorderSide(color: scheme.outlineVariant, width: 1.2),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          textStyle: _inter(fontWeight: FontWeight.w600),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: scheme.primary,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          textStyle: _inter(fontWeight: FontWeight.w600),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: scheme.surfaceContainerHighest.withValues(alpha: 0.6),
        border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14), borderSide: BorderSide(color: scheme.outlineVariant)),
        enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14), borderSide: BorderSide(color: scheme.outlineVariant)),
        focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14), borderSide: BorderSide(color: scheme.primary, width: 1.4)),
        errorBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14), borderSide: BorderSide(color: scheme.error, width: 1.2)),
        focusedErrorBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14), borderSide: BorderSide(color: scheme.error, width: 1.4)),
        disabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: BorderSide(color: scheme.outlineVariant.withValues(alpha: 0.6))),
        isDense: true,
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        hintStyle: _inter(color: scheme.onSurfaceVariant, fontSize: 14),
        labelStyle: _inter(color: scheme.onSurfaceVariant, fontSize: 14, fontWeight: FontWeight.w500),
        floatingLabelStyle: _inter(color: scheme.primary, fontSize: 14, fontWeight: FontWeight.w600),
        errorStyle: _inter(color: scheme.error, fontSize: 12, fontWeight: FontWeight.w500),
        helperStyle: _inter(color: scheme.onSurfaceVariant, fontSize: 12),
      ),
      cardTheme: CardThemeData(
        elevation: 1,
        shadowColor: scheme.shadow.withValues(alpha: 0.08),
        surfaceTintColor: Colors.transparent,
        color: scheme.surfaceContainerLow,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        margin: EdgeInsets.zero,
      ),
      chipTheme: ChipThemeData(
        backgroundColor: scheme.surfaceContainerHigh,
        selectedColor: scheme.primaryContainer,
        checkmarkColor: scheme.onPrimaryContainer,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
        side: BorderSide.none,
        labelStyle: _inter(fontWeight: FontWeight.w600, fontSize: 13),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      ),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        backgroundColor: scheme.inverseSurface,
        contentTextStyle: _inter(color: scheme.onInverseSurface, fontWeight: FontWeight.w500),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        elevation: 4,
      ),
      segmentedButtonTheme: SegmentedButtonThemeData(
        style: ButtonStyle(
          backgroundColor: WidgetStateProperty.resolveWith((states) {
            if (states.contains(WidgetState.selected)) return scheme.primaryContainer;
            return scheme.surfaceContainerHigh;
          }),
          foregroundColor: WidgetStateProperty.resolveWith((states) {
            if (states.contains(WidgetState.selected)) return scheme.onPrimaryContainer;
            return scheme.onSurfaceVariant;
          }),
          side: WidgetStatePropertyAll(BorderSide.none),
          shape: WidgetStatePropertyAll(RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
          textStyle: WidgetStatePropertyAll(_inter(fontWeight: FontWeight.w600, fontSize: 13)),
        ),
      ),
      dividerTheme: DividerThemeData(color: scheme.outlineVariant.withValues(alpha: 0.4), thickness: 1, space: 1),
      progressIndicatorTheme: ProgressIndicatorThemeData(
        color: scheme.primary,
        linearTrackColor: scheme.surfaceContainerHigh,
        circularTrackColor: scheme.surfaceContainerHigh,
      ),
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: scheme.primaryContainer,
        foregroundColor: scheme.onPrimaryContainer,
        elevation: 3,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
      iconButtonTheme: IconButtonThemeData(
        style: ButtonStyle(
          foregroundColor: WidgetStateProperty.resolveWith((states) {
            if (states.contains(WidgetState.disabled)) return scheme.onSurfaceVariant.withValues(alpha: 0.38);
            return null;
          }),
          overlayColor: WidgetStatePropertyAll(scheme.primary.withValues(alpha: 0.08)),
        ),
      ),
      listTileTheme: ListTileThemeData(
        iconColor: scheme.onSurfaceVariant,
        titleTextStyle: _inter(
            fontSize: 14, fontWeight: FontWeight.w600, color: scheme.onSurface),
        subtitleTextStyle: _inter(
            fontSize: 12, fontWeight: FontWeight.w400, color: scheme.onSurfaceVariant),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
      checkboxTheme: CheckboxThemeData(
        fillColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) return scheme.primary;
          return null;
        }),
        checkColor: WidgetStatePropertyAll(scheme.onPrimary),
        side: BorderSide(color: scheme.outline, width: 1.4),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
      ),
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) return scheme.onPrimary;
          return scheme.outline;
        }),
        trackColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) return scheme.primary;
          return scheme.surfaceContainerHighest;
        }),
      ),
      tabBarTheme: TabBarThemeData(
        labelColor: scheme.primary,
        unselectedLabelColor: scheme.onSurfaceVariant,
        indicatorColor: scheme.primary,
        indicatorSize: TabBarIndicatorSize.tab,
        labelStyle: _inter(fontWeight: FontWeight.w700, fontSize: 13),
        unselectedLabelStyle: _inter(fontWeight: FontWeight.w500, fontSize: 13),
      ),
      bottomSheetTheme: BottomSheetThemeData(
        backgroundColor: scheme.surfaceContainerLow,
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
        elevation: 8,
        dragHandleColor: scheme.outlineVariant,
        dragHandleSize: const Size(32, 4),
        showDragHandle: true,
      ),
      dialogTheme: DialogThemeData(
        backgroundColor: scheme.surfaceContainerLow,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        elevation: 8,
      ),
    );
  }
}
