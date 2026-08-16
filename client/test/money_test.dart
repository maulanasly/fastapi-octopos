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
      expect(formatCents(450), r'$4.50');
      expect(formatCents(10000), r'$100.00');
      expect(formatCents(5), r'$0.05');
      expect(formatCents(0), r'$0.00');
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
