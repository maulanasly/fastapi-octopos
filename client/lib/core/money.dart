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
///
/// Rounds instead of truncating: binary floats like 58.30 sit just below
/// 5830 (5829.999...), and truncation silently loses the cent.
int centsFromApi(num? value) => ((value ?? 0) * 100).round();

/// User-typed amount string (e.g. `"4.50"`) -> integer cents (450).
///
/// Single conversion path for every money input field so display-time
/// validation and submit-time payload always agree.
int centsFromInput(String input) => ((double.tryParse(input) ?? 0) * 100).round();

String _currency = 'USD';
String _numberFormat = 'en_US';

/// Active display currency code (e.g. 'USD', 'IDR').
String get currentCurrency => _currency;

/// Sets the active display currency and number format (e.g. `IDR` /
/// `id_ID`). Falls back to `USD` / `en_US` defaults until called.
void configureMoney({required String currency, required String numberFormat}) {
  _currency = currency;
  _numberFormat = numberFormat;
}

/// Symbol for a currency code (e.g. 'USD' -> '$', 'IDR' -> 'Rp').
String currencySymbol(String currency) {
  switch (currency) {
    case 'IDR':
      return 'Rp';
    case 'EUR':
      return '€';
    case 'GBP':
      return '£';
    case 'SGD':
      return r'S$';
    case 'JPY':
      return '¥';
    case 'MYR':
      return 'RM';
    case 'AUD':
      return r'A$';
    default:
      return r'$';
  }
}

/// Integer cents -> display string (e.g. `$4.50`, `Rp 4.500` for IDR).
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
  final number = NumberFormat('#,##0.00', locale)
    ..minimumFractionDigits = decimalDigits
    ..maximumFractionDigits = decimalDigits;
  final symbol = currencySymbol(_currency);
  // Indonesian convention: a space between "Rp" and the amount
  // (e.g. `Rp 4.500`); other currencies attach the symbol directly.
  final separator = _currency == 'IDR' ? ' ' : '';
  return '$symbol$separator${number.format(value)}';
}

/// Integer cents -> bare string with two decimals (e.g. `4.50`).
String centsToApi(int cents) {
  final dollars = cents ~/ 100;
  final rem = cents % 100;
  return '$dollars.${rem.toString().padLeft(2, '0')}';
}
