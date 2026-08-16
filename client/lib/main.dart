import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app/router.dart';
import 'app/theme.dart';
import 'app/theme_controller.dart';
import 'core/api_client.dart';
import 'core/config.dart';
import 'core/localization_controller.dart';

void main() {
  runApp(const ProviderScope(child: OctoPosApp()));
}

class OctoPosApp extends ConsumerWidget {
  const OctoPosApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Trigger the sync bootstrap (catalog delta pull) on startup.
    ref.watch(syncBootstrapProvider);
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

/// Boots the API session (token restore) once at app start.
class _SyncBootstrap extends Notifier<bool> {
  @override
  bool build() {
    Future.microtask(() async {
      await ref.read(apiClientProvider).restore();
    });
    return true;
  }
}

final syncBootstrapProvider = NotifierProvider<_SyncBootstrap, bool>(
  _SyncBootstrap.new,
);
