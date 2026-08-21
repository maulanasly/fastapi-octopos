/// Local persistence: draft cart + catalog sync watermark.
///
/// Uses shared_preferences so a mid-order browser refresh doesn't lose
/// the sale; the watermark enables delta catalog pulls on later starts.
library;

import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _cartKey = 'octopos_cart';
const _watermarkKey = 'octopos_sync_watermark';

final localStoreProvider = Provider<LocalStore>((ref) => LocalStore());
class PersistedCart {
  final Map<int, int> quantities; // productId -> quantity
  final int? customerId;
  final String promotionCode;
  final int redeemPoints;

  const PersistedCart({
    required this.quantities,
    this.customerId,
    this.promotionCode = '',
    this.redeemPoints = 0,
  });

  Map<String, dynamic> toJson() => {
    'lines': [
      for (final entry in quantities.entries)
        {'product_id': entry.key, 'quantity': entry.value},
    ],
    if (customerId != null) 'customer_id': customerId,
    if (promotionCode.isNotEmpty) 'promotion_code': promotionCode,
    if (redeemPoints > 0) 'redeem_points': redeemPoints,
  };

  static PersistedCart? fromJson(Map<String, dynamic> json) {
    final lines = json['lines'];
    if (lines is! List || lines.isEmpty) return null;
    final quantities = <int, int>{};
    for (final line in lines) {
      if (line is Map && line['product_id'] is int && line['quantity'] is int) {
        quantities[line['product_id'] as int] = line['quantity'] as int;
      }
    }
    if (quantities.isEmpty) return null;
    return PersistedCart(
      quantities: quantities,
      customerId: json['customer_id'] as int?,
      promotionCode: json['promotion_code'] as String? ?? '',
      redeemPoints: json['redeem_points'] as int? ?? 0,
    );
  }
}

class LocalStore {
  Future<void> saveCart(PersistedCart cart) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_cartKey, jsonEncode(cart.toJson()));
  }

  Future<PersistedCart?> loadCart() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_cartKey);
    if (raw == null || raw.isEmpty) return null;
    try {
      return PersistedCart.fromJson(jsonDecode(raw) as Map<String, dynamic>);
    } catch (_) {
      return null;
    }
  }

  Future<void> clearCart() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_cartKey);
  }

  Future<String?> readWatermark() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_watermarkKey);
  }

  Future<void> writeWatermark(String iso) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_watermarkKey, iso);
  }

  Future<void> clearWatermark() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_watermarkKey);
  }

  /// Wipes per-user local state on sign-out: a draft cart or catalog
  /// watermark must never leak into the next user's session.
  Future<void> clearSessionData() async {
    await clearCart();
    await clearWatermark();
  }
}
