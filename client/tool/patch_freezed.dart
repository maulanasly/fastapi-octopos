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
    // Patch only constructor lines (contain "const _" ), keep @override fields intact.
    final lines = text.split('\n');
    for (var i = 0; i < lines.length; i++) {
      final line = lines[i];
      if (line.contains('const _') && line.contains('final')) {
        // Remove "final " before List/String/int etc in constructor params
        // Handles both "final  " (double space) and "final " and annotation case "@JsonKey(...) final  List"
        var patched = line.replaceAll('final  ', '');
        patched = patched.replaceAll('final ', '');
        lines[i] = patched;
      }
    }
    text = lines.join('\n');
    if (text != original) {
      file.writeAsStringSync(text);
      // ignore: avoid_print
      print('patched $path');
    }
  }
}
