import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app/router.dart';
import 'app/theme.dart';
import 'app/theme_controller.dart';
import 'core/config.dart';
import 'core/localization_controller.dart';

void main() {
  runApp(const ProviderScope(child: OctoPosApp()));
}

class OctoPosApp extends ConsumerWidget {
  const OctoPosApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Activate per-user localization (region fetch on sign-in).
    ref.watch(localizationControllerProvider);

    final router = ref.watch(routerProvider);
    final themeMode = ref.watch(themeModeProvider);
    return MaterialApp.router(
      title: AppConfig.appTitle,
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: themeMode,
      routerConfig: router,
      debugShowCheckedModeBanner: false,
    );
  }
}
