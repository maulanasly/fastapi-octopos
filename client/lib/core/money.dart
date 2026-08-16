/// Money helpers.
///
/// The backend stores amounts as DECIMAL(12,2) and serializes floats; the
/// client works in integer cents to avoid float drift, matching the
/// backend's 2-decimal quantization exactly.
///
/// Display formatting follows the backend [LocalizationSetting]: call
/// [configureMoney] once a session is active (e.g. after login) so amounts
/// render with the right currency symbol and regional number format
/// (e.g. `Rp4.500` for Indonesia instead of `$4.50`).
library;

import 'package:intl/intl.dart';

/// Backend float (e.g. `4.50`) -> integer cents (450).
int centsFromApi(num? value) => (value ?? 0) * 100 ~/ 1;

String _currency = 'USD';
String _numberFormat = 'en_US';

/// Sets the active display currency and number format (e.g. `IDR` /
/// `id_ID`). Falls back to `USD` / `en_US` defaults until called.
void configureMoney({required String currency, required String numberFormat}) {
  _currency = currency;
  _numberFormat = numberFormat;
}

String _currencySymbol(String currency) {
  switch (currency) {
    case 'IDR':
      return 'Rp';
    case 'EUR':
      return '€';
    case 'GBP':
      return '£';
    default:
      return r'$';
  }
}

/// Integer cents -> display string (e.g. `$4.50`, `Rp4.500` for IDR).
String formatCents(int cents) {
  // id_ID uses '.' as the thousands separator and ',' as the decimal one;
  // everything else uses the en_US layout.
  final locale = _numberFormat == 'id_ID' ? 'id_ID' : 'en_US';
  // The Rupiah has no circulating subunit; drop the fraction like the
  // backend (which truncates, e.g. Rp4.55 -> Rp4).
  final decimalDigits = _currency == 'IDR' ? 0 : 2;
  final value = _currency == 'IDR'
      ? (cents / 100).floorToDouble()
      : cents / 100;
  final f = NumberFormat.currency(
    locale: locale,
    symbol: _currencySymbol(_currency),
    decimalDigits: decimalDigits,
  );
  return f.format(value);
}

/// Integer cents -> bare string with two decimals (e.g. `4.50`).
String centsToApi(int cents) {
  final dollars = cents ~/ 100;
  final rem = cents % 100;
  return '$dollars.${rem.toString().padLeft(2, '0')}';
}
