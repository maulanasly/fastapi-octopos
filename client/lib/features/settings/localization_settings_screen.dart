/// Tenant localization settings (settings:manage).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/errors.dart';
import '../../core/models.dart';
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
  final _language = TextEditingController();
  final _timezone = TextEditingController();
  final _currency = TextEditingController();
  final _dateFormat = TextEditingController();
  final _numberFormat = TextEditingController();
  final _countryCode = TextEditingController();

  @override
  void initState() {
    super.initState();
    _future = ref.read(localizationRepositoryProvider).settings();
  }

  Future<void> _save() async {
    final s = ref.read(stringsProvider);
    try {
      await ref.read(localizationRepositoryProvider).updateSettings({
        if (_language.text.trim().isNotEmpty) 'language': _language.text.trim(),
        if (_timezone.text.trim().isNotEmpty) 'timezone': _timezone.text.trim(),
        if (_currency.text.trim().isNotEmpty) 'currency': _currency.text.trim(),
        if (_dateFormat.text.trim().isNotEmpty)
          'date_format': _dateFormat.text.trim(),
        if (_numberFormat.text.trim().isNotEmpty)
          'number_format': _numberFormat.text.trim(),
        if (_countryCode.text.trim().isNotEmpty)
          'country_code': _countryCode.text.trim(),
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

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    return Scaffold(
      appBar: AppBar(
        title: Text(s.of('localizationSettings')),
        actions: [
          IconButton(
            tooltip: s.of('save'),
            onPressed: _save,
            icon: const Icon(Icons.save_outlined),
          ),
        ],
      ),
      body: FutureBuilder<LocalizationSetting>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text(friendlyError(snapshot.error!, s)));
          }
          final setting = snapshot.data!;
          if (_language.text.isEmpty) {
            _language.text = setting.language;
            _timezone.text = setting.timezone;
            _currency.text = setting.currency;
            _dateFormat.text = setting.dateFormat;
            _numberFormat.text = setting.numberFormat;
            _countryCode.text = setting.countryCode;
          }
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _field(s.of('language'), _language),
              _field(s.of('timezone'), _timezone),
              _field(s.of('currency'), _currency),
              _field(s.of('dateFormat'), _dateFormat),
              _field(s.of('numberFormat'), _numberFormat),
              _field(s.of('countryCode'), _countryCode),
              const SizedBox(height: 16),
              FilledButton.icon(
                onPressed: _save,
                icon: const Icon(Icons.save_outlined),
                label: Text(s.of('save')),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _field(String label, TextEditingController controller) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: TextField(
        controller: controller,
        decoration: InputDecoration(labelText: label, isDense: true),
      ),
    );
  }
}
