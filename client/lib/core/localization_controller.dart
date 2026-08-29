/// Per-user localization state: fetches the effective region settings
/// after sign-in and feeds the money/dates formatters + Accept-Language.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'api_client.dart';
import 'api_repositories.dart';
import 'auth_controller.dart';
import 'dates.dart';
import 'errors.dart';
import 'models.dart';
import 'money.dart';
import 'strings.dart';

class LocalizationState {
  final LocalizationSetting? setting;
  final bool loading;
  final String? error;

  const LocalizationState({this.setting, this.loading = false, this.error});

  String get language => setting?.language ?? 'en';
}

class LocalizationController extends Notifier<LocalizationState> {
  @override
  LocalizationState build() {
    ref.listen<AuthState>(authControllerProvider, (prev, next) {
      if (next.status == AuthStatus.signedIn) {
        load();
      } else if (next.status == AuthStatus.signedOut) {
        _reset();
      }
    });
    return const LocalizationState();
  }

  Future<void> load() async {
    state = const LocalizationState(loading: true);
    try {
      final setting = await ref.read(localizationRepositoryProvider).me();
      _apply(setting);
      state = LocalizationState(setting: setting);
    } catch (e) {
      state = LocalizationState(
        error: friendlyError(e, ref.read(stringsProvider)),
      );
    }
  }

  Future<void> setRegion(String? region) async {
    state = const LocalizationState(loading: true);
    try {
      final setting = await ref
          .read(localizationRepositoryProvider)
          .updateRegion(region);
      _apply(setting);
      state = LocalizationState(setting: setting);
    } catch (e) {
      state = LocalizationState(
        error: friendlyError(e, ref.read(stringsProvider)),
      );
      rethrow;
    }
  }

  void _apply(LocalizationSetting setting) {
    configureMoney(
      currency: setting.currency,
      numberFormat: setting.numberFormat,
    );
    // Keep Riverpod configs in sync with globals so widgets watching
    // providers rebuild correctly.
    try {
      ref.read(moneyConfigProvider.notifier).configure(
        currency: setting.currency,
        numberFormat: setting.numberFormat,
      );
    } catch (_) {}
    configureDates(timezone: setting.timezone, dateFormat: setting.dateFormat);
    try {
      ref.read(dateConfigProvider.notifier).configure(
        timezone: setting.timezone,
        dateFormat: setting.dateFormat,
      );
    } catch (_) {}
    ref.read(apiClientProvider).session.language = setting.language;
  }

  void _reset() {
    configureMoney(currency: 'USD', numberFormat: 'en_US');
    try {
      ref.read(moneyConfigProvider.notifier).reset();
    } catch (_) {}
    configureDates(timezone: 'UTC', dateFormat: '%Y-%m-%d %H:%M:%S');
    try {
      ref.read(dateConfigProvider.notifier).reset();
    } catch (_) {}
    ref.read(apiClientProvider).session.language = null;
    state = const LocalizationState();
  }
}

final localizationControllerProvider =
    NotifierProvider<LocalizationController, LocalizationState>(
      LocalizationController.new,
    );
