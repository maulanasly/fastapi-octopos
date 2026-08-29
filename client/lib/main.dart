import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:workmanager/workmanager.dart';

import 'app/router.dart';
import 'app/theme.dart';
import 'app/theme_controller.dart';
import 'core/config.dart';
import 'core/localization_controller.dart';
import 'core/sync/auto_sync.dart';
import 'core/sync/workmanager.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Register background work (no-op if not supported like web)
  try {
    await Workmanager().initialize(callbackDispatcher, isInDebugMode: false);
    await Workmanager().registerPeriodicTask(
      syncTask,
      syncTask,
      frequency: const Duration(minutes: 15),
      constraints: Constraints(networkType: NetworkType.connected),
      existingWorkPolicy: ExistingWorkPolicy.keep,
    );
    await Workmanager().registerPeriodicTask(
      outboxTask,
      outboxTask,
      frequency: const Duration(minutes: 15),
      constraints: Constraints(networkType: NetworkType.connected),
      existingWorkPolicy: ExistingWorkPolicy.keep,
    );
  } catch (_) {
    // Workmanager not available on web/desktop
  }
  runApp(const ProviderScope(child: OctoPosApp()));
}

class OctoPosApp extends ConsumerWidget {
  const OctoPosApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Activate per-user localization (region fetch on sign-in).
    ref.watch(localizationControllerProvider);
    // Foreground auto-sync when connectivity restores.
    ref.watch(autoSyncProvider);

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
