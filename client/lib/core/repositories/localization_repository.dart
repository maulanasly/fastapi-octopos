library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api_client.dart';
import '../models.dart';

final localizationRepositoryProvider = Provider<LocalizationRepository>(
  (ref) => LocalizationRepository(ref.watch(apiClientProvider)),
);

/// Supported regional presets (fetched once).
final regionListProvider = FutureProvider<List<LocalizationRegion>>((ref) {
  return ref.watch(localizationRepositoryProvider).regions();
});

/// Supported values for tenant localization settings (fetched once).
final localizationOptionsProvider = FutureProvider<LocalizationOptions>((ref) {
  return ref.watch(localizationRepositoryProvider).options();
});

class LocalizationRepository {
  final ApiClient api;
  LocalizationRepository(this.api);

  /// Global (admin-managed) localization settings.
  Future<LocalizationSetting> settings() async {
    final resp = await api.dio.get<Map<String, dynamic>>('/localization/');
    return LocalizationSetting.fromJson(resp.data!);
  }

  /// Update the tenant-level localization settings (settings:manage).
  Future<LocalizationSetting> updateSettings(Map<String, dynamic> body) async {
    final resp = await api.dio.put<Map<String, dynamic>>(
      '/localization/',
      data: body,
    );
    return LocalizationSetting.fromJson(resp.data!);
  }

  /// Supported values for the tenant localization settings (settings:manage).
  Future<LocalizationOptions> options() async {
    final resp = await api.dio.get<Map<String, dynamic>>(
      '/localization/options',
    );
    return LocalizationOptions.fromJson(resp.data!);
  }

  /// Effective per-user localization (region preset or global default).
  Future<LocalizationSetting> me() async {
    final resp = await api.dio.get<Map<String, dynamic>>('/localization/me');
    return LocalizationSetting.fromJson(resp.data!);
  }

  /// Supported regional presets.
  Future<List<LocalizationRegion>> regions() async {
    final resp = await api.dio.get<List<dynamic>>('/localization/regions');
    return resp.data!
        .map((e) => LocalizationRegion.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Switch the caller's region preset (null resets to global default).
  Future<LocalizationSetting> updateRegion(String? region) async {
    final resp = await api.dio.put<Map<String, dynamic>>(
      '/localization/me',
      data: {'region': region},
    );
    return LocalizationSetting.fromJson(resp.data!);
  }
}
