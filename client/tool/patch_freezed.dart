import 'dart:io';

/// Patches freezed 3.2 generated code that emits `final` in const constructor
/// params (e.g. `const _CatalogDelta({final  List<...>}`) which is not valid
/// Dart 3.13 syntax for const constructors. The patch removes `final  ` only
/// from constructor param lists, keeping `final` on fields.
///
/// Run after `dart run build_runner build`:
///   dart tool/patch_freezed.dart
void main() {
  final files = [
    'lib/core/models/catalog.freezed.dart',
    'lib/core/models/auth.freezed.dart',
    'lib/core/models/localization.freezed.dart',
  ];
  for (final path in files) {
    final file = File(path);
    if (!file.existsSync()) continue;
    var text = file.readAsStringSync();
    final original = text;
    // Only patch constructor signatures: const _X({ ... })
    text = text.replaceAll(', final  ', ', ');
    text = text.replaceAll(', final ', ', ');
    text = text.replaceAll('({final  ', '({');
    text = text.replaceAll('({final ', '({');
    text = text.replaceAll('({required final  ', '({required ');
    text = text.replaceAll('({required final ', '({required ');
    // Also handle "@JsonKey(...) final  " inside constructor params
    // Already covered by ", final  "
    if (text != original) {
      file.writeAsStringSync(text);
      // ignore: avoid_print
      print('patched $path');
    }
  }
}
