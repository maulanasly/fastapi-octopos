import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/money.dart';

void main() {
  group('centsFromApi', () {
    test('converts backend float to integer cents', () {
      expect(centsFromApi(4.5), 450);
      expect(centsFromApi(100.0), 10000);
      expect(centsFromApi(0), 0);
      expect(centsFromApi(null), 0);
      expect(centsFromApi(0.01), 1);
    });
  });

  group('formatCents', () {
    test('formats with two decimals and currency symbol', () {
      configureMoney(currency: 'USD', numberFormat: 'en_US');
      expect(formatCents(450), r'$4.50');
      expect(formatCents(10000), r'$100.00');
      expect(formatCents(5), r'$0.05');
      expect(formatCents(0), r'$0.00');
    });

    test('defaults to en_US/USD before configureMoney', () {
      configureMoney(currency: 'USD', numberFormat: 'en_US');
      expect(formatCents(450), r'$4.50');
    });

    test('formats IDR with Indonesian number format', () {
      configureMoney(currency: 'IDR', numberFormat: 'id_ID');
      expect(formatCents(450), 'Rp 4');
      expect(formatCents(450000), 'Rp 4.500');
      expect(formatCents(450000000), 'Rp 4.500.000');
      expect(formatCents(0), 'Rp 0');
    });

    test('formats IDR with en_US number format', () {
      configureMoney(currency: 'IDR', numberFormat: 'en_US');
      expect(formatCents(450000), 'Rp 4,500');
      expect(formatCents(0), 'Rp 0');
    });

    test('formats USD with Indonesian number format', () {
      configureMoney(currency: 'USD', numberFormat: 'id_ID');
      expect(formatCents(450), r'$4,50');
      expect(formatCents(450000), r'$4.500,00');
    });

    test('resets to defaults on logout-style reconfigure', () {
      configureMoney(currency: 'IDR', numberFormat: 'id_ID');
      configureMoney(currency: 'USD', numberFormat: 'en_US');
      expect(formatCents(450), r'$4.50');
    });
  });

  group('centsToApi', () {
    test('produces two-decimal string for API payloads', () {
      expect(centsToApi(450), '4.50');
      expect(centsToApi(10000), '100.00');
      expect(centsToApi(7), '0.07');
      expect(centsToApi(0), '0.00');
    });
  });
}
