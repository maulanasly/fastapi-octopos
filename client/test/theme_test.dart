import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/app/theme.dart';
import 'package:octopos_client/app/theme_controller.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('AppTheme', () {
    test('light is the default theme mode', () {
      expect(AppTheme.defaultThemeMode, ThemeMode.light);
    });

    test('light scheme uses the Market Teal brand primary', () {
      final scheme = AppTheme.light.colorScheme;
      expect(scheme.primary, const Color(0xFF0F766E));
      expect(scheme.onPrimary, Colors.white);
      expect(scheme.secondary, const Color(0xFF0284C7));
      expect(scheme.tertiary, const Color(0xFFB45309));
      expect(scheme.error, const Color(0xFFDC2626));
      expect(scheme.surface, const Color(0xFFF8FAF9));
    });

    test('dark scheme uses dark-variant brand roles', () {
      final scheme = AppTheme.dark.colorScheme;
      expect(scheme.brightness, Brightness.dark);
      expect(scheme.primary, const Color(0xFF5EEAD4));
      expect(scheme.onPrimary, const Color(0xFF042F2E));
    });
  });

  group('ThemeModeController', () {
    test('defaults to light without a saved preference', () async {
      SharedPreferences.setMockInitialValues({});
      final container = ProviderContainer();
      addTearDown(container.dispose);

      expect(container.read(themeModeProvider), ThemeMode.light);
    });

    test('toggle flips the mode and persists it', () async {
      SharedPreferences.setMockInitialValues({});
      final container = ProviderContainer();
      addTearDown(container.dispose);
      final notifier = container.read(themeModeProvider.notifier);

      await notifier.toggle();
      expect(container.read(themeModeProvider), ThemeMode.dark);
      var prefs = await SharedPreferences.getInstance();
      expect(prefs.getString('octopos_theme_mode'), 'dark');

      await notifier.toggle();
      expect(container.read(themeModeProvider), ThemeMode.light);
      prefs = await SharedPreferences.getInstance();
      expect(prefs.getString('octopos_theme_mode'), 'light');
    });

    test('restores a saved dark preference', () async {
      SharedPreferences.setMockInitialValues({'octopos_theme_mode': 'dark'});
      final container = ProviderContainer();
      addTearDown(container.dispose);

      // restore() loads the pref asynchronously; poll until applied.
      for (var i = 0; i < 50; i++) {
        if (container.read(themeModeProvider) == ThemeMode.dark) break;
        await Future<void>.delayed(const Duration(milliseconds: 5));
      }
      expect(container.read(themeModeProvider), ThemeMode.dark);
    });
  });
}
