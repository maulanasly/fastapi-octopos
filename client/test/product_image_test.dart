import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:octopos_client/core/colors.dart';
import 'package:octopos_client/core/models.dart';

void main() {
  group('colorFromHex', () {
    test('parses #RRGGBB', () {
      expect(colorFromHex('#E8F5E9'), const Color(0xFFE8F5E9));
      expect(colorFromHex('#ff0000'), const Color(0xFFFF0000));
    });

    test('returns null for invalid values', () {
      expect(colorFromHex(null), isNull);
      expect(colorFromHex(''), isNull);
      expect(colorFromHex('green'), isNull);
      expect(colorFromHex('#FFF'), isNull);
      expect(colorFromHex('#GGGGGG'), isNull);
    });
  });

  group('textColorOn', () {
    test('dark text on light background', () {
      expect(textColorOn(const Color(0xFFE8F5E9)), Colors.black87);
    });

    test('white text on dark background', () {
      expect(textColorOn(const Color(0xFF0F766E)), Colors.white);
    });
  });

  group('model parsing', () {
    test('product parses image_url', () {
      final product = Product.fromJson(const {
        'id': 1,
        'name': 'Latte',
        'sku': 'L',
        'price': 4.5,
        'stock_quantity': 5,
        'min_stock': 0,
        'reorder_point': 0,
        'lead_time_days': 0,
        'image_url': '/media/products/1_abc.png',
      });
      expect(product.imageUrl, '/media/products/1_abc.png');
    });

    test('category parses color and tolerates missing', () {
      final colored = Category.fromJson(const {
        'id': 1,
        'name': 'Beverages',
        'color': '#E8F5E9',
      });
      expect(colored.color, '#E8F5E9');

      final plain = Category.fromJson(const {'id': 2, 'name': 'Food'});
      expect(plain.color, isNull);
    });
  });
}
