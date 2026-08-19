/// Tenant localization settings (settings:manage).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../core/api_repositories.dart';
import '../../core/dates.dart';
import '../../core/errors.dart';
import '../../core/models.dart';
import '../../core/money.dart';
import '../../core/strings.dart';

class LocalizationSettingsScreen extends ConsumerStatefulWidget {
  const LocalizationSettingsScreen({super.key});

  @override
  ConsumerState<LocalizationSettingsScreen> createState() =>
      _LocalizationSettingsScreenState();
}

class _LocalizationSettingsScreenState
    extends ConsumerState<LocalizationSettingsScreen> {
  late Future<LocalizationSetting> _future;
  LocalizationSetting? _setting;
  String? _language;
  String? _timezone;
  String? _currency;
  String? _dateFormat;
  String? _numberFormat;
  String? _countryCode;

  @override
  void initState() {
    super.initState();
    _future = ref.read(localizationRepositoryProvider).settings();
  }

  Future<void> _save() async {
    final s = ref.read(stringsProvider);
    final setting = _setting;
    if (setting == null) return;
    try {
      await ref.read(localizationRepositoryProvider).updateSettings({
        'language': _language ?? setting.language,
        'timezone': _timezone ?? setting.timezone,
        'currency': _currency ?? setting.currency,
        'date_format': _dateFormat ?? setting.dateFormat,
        'number_format': _numberFormat ?? setting.numberFormat,
        'country_code': _countryCode ?? setting.countryCode,
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(s.of('settingsSaved'))),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(friendlyError(e, s))));
      }
    }
  }

  void _applyPreset(LocalizationRegion preset) {
    setState(() {
      _language = preset.language;
      _timezone = preset.timezone;
      _currency = preset.currency;
      _dateFormat = preset.dateFormat;
      _numberFormat = preset.numberFormat;
      _countryCode = preset.countryCode;
    });
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    return Scaffold(
      appBar: AppBar(title: Text(s.of('localizationSettings'))),
      body: FutureBuilder<LocalizationSetting>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text(friendlyError(snapshot.error!, s)));
          }
          _setting ??= snapshot.data!;
          final setting = _setting!;
          return ref.watch(localizationOptionsProvider).when(
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (e, _) => Center(child: Text(friendlyError(e, s))),
                data: (options) => _buildForm(setting, options, s),
              );
        },
      ),
    );
  }

  Widget _buildForm(
    LocalizationSetting setting,
    LocalizationOptions options,
    AppStrings s,
  ) {
    final regions = ref.watch(regionListProvider).value ?? const [];
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (regions.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: DropdownButtonFormField<String>(
              initialValue: null,
              decoration: InputDecoration(
                labelText: s.of('preset'),
                helperText: s.of('presetHint'),
                isDense: true,
              ),
              items: [
                for (final region in regions)
                  DropdownMenuItem(
                    value: region.countryCode,
                    child: Text(
                      '${region.countryCode} · ${region.language} · '
                      '${currencySymbol(region.currency)}',
                    ),
                  ),
              ],
              onChanged: (code) {
                for (final region in regions) {
                  if (region.countryCode == code) {
                    _applyPreset(region);
                  }
                }
              },
            ),
          ),
        _dropdown(
          s.of('language'),
          _language ?? setting.language,
          options.languages,
          (v) => setState(() => _language = v),
        ),
        _dropdown(
          s.of('countryCode'),
          _countryCode ?? setting.countryCode,
          options.countryCodes,
          (v) => setState(() => _countryCode = v),
        ),
        _dropdown(
          s.of('currency'),
          _currency ?? setting.currency,
          options.currencies,
          (v) => setState(() => _currency = v),
          itemBuilder: (v) => '$v · ${currencySymbol(v)}',
        ),
        _dropdown(
          s.of('timezone'),
          _timezone ?? setting.timezone,
          options.timezones,
          (v) => setState(() => _timezone = v),
        ),
        _dropdown(
          s.of('numberFormat'),
          _numberFormat ?? setting.numberFormat,
          options.numberFormats,
          (v) => setState(() => _numberFormat = v),
        ),
        _dropdown(
          s.of('dateFormat'),
          _dateFormat ?? setting.dateFormat,
          options.dateFormats,
          (v) => setState(() => _dateFormat = v),
          itemBuilder: _dateFormatPreview,
        ),
        const SizedBox(height: 16),
        FilledButton.icon(
          onPressed: _save,
          icon: const Icon(Icons.save_outlined),
          label: Text(s.of('save')),
        ),
      ],
    );
  }

  /// Stable preview of a strftime format (e.g. `2026-08-19 14:30:00`).
  String _dateFormatPreview(String format) {
    final sample = DateTime.utc(2026, 8, 19, 14, 30);
    return DateFormat(toIntlPattern(format)).format(sample);
  }

  Widget _dropdown(
    String label,
    String value,
    List<String> values,
    ValueChanged<String> onChanged, {
    String Function(String value)? itemBuilder,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: DropdownButtonFormField<String>(
        initialValue: value,
        decoration: InputDecoration(labelText: label, isDense: true),
        items: [
          // A stored value outside the supported list (e.g. a legacy setting
          // entered before selects were enforced) must still be selectable,
          // otherwise DropdownButtonFormField throws on a value with no item.
          if (!values.contains(value))
            DropdownMenuItem(
              value: value,
              child: Text(itemBuilder?.call(value) ?? value),
            ),
          for (final v in values)
            DropdownMenuItem(value: v, child: Text(itemBuilder?.call(v) ?? v)),
        ],
        onChanged: (v) {
          if (v != null) onChanged(v);
        },
      ),
    );
  }
}
