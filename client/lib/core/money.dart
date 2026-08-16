/// Money helpers.
///
/// The backend stores amounts as DECIMAL(12,2) and serializes floats; the
/// client works in integer cents to avoid float drift, matching the
/// backend's 2-decimal quantization exactly.
library;

import 'package:intl/intl.dart';

/// Backend float (e.g. `4.50`) -> integer cents (450).
int centsFromApi(num? value) => (value ?? 0) * 100 ~/ 1;

/// Integer cents -> display string (e.g. `$4.50`).
String formatCents(int cents) {
  final f = NumberFormat.currency(locale: 'en_US', symbol: r'$');
  return f.format(cents / 100);
}

/// Integer cents -> bare string with two decimals (e.g. `4.50`).
String centsToApi(int cents) {
  final dollars = cents ~/ 100;
  final rem = cents % 100;
  return '$dollars.${rem.toString().padLeft(2, '0')}';
}
