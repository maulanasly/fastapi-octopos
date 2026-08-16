/// Per-user localization state: fetches the effective region settings
/// after sign-in and feeds the money/dates formatters + Accept-Language.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'api_client.dart';
import 'api_repositories.dart';
import 'auth_controller.dart';
import 'models.dart';
import 'money.dart';

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
      state = LocalizationState(error: e.toString());
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
      state = LocalizationState(error: e.toString());
      rethrow;
    }
  }

  void _apply(LocalizationSetting setting) {
    configureMoney(
      currency: setting.currency,
      numberFormat: setting.numberFormat,
    );
    ref.read(apiClientProvider).session.language = setting.language;
  }

  void _reset() {
    configureMoney(currency: 'USD', numberFormat: 'en_US');
    ref.read(apiClientProvider).session.language = null;
    state = const LocalizationState();
  }
}

final localizationControllerProvider =
    NotifierProvider<LocalizationController, LocalizationState>(
      LocalizationController.new,
    );
