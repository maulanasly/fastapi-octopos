/// Unified outline icon set — Market Teal ink aesthetic.
/// All icons are Material outlined, 20-22 size, 1.8 stroke equivalent
/// via outlined variant. Centralizes ~100 Icons.* usages and admin FA
/// divergence (fa-*). Use via AppIcons.* instead of raw Icons.*.
library;

import 'package:flutter/material.dart';

abstract final class AppIcons {
  // Navigation (home_shell)
  static const IconData pos = Icons.point_of_sale_outlined;
  static const IconData serving = Icons.room_service_outlined;
  static const IconData tracking = Icons.route_outlined;
  static const IconData orders = Icons.receipt_long_outlined;
  static const IconData inventory = Icons.inventory_2_outlined;
  static const IconData purchasing = Icons.shopping_cart_outlined;
  static const IconData products = Icons.edit_outlined;
  static const IconData customers = Icons.people_alt_outlined;
  static const IconData promotions = Icons.percent_outlined;
  static const IconData taxes = Icons.receipt_outlined;
  static const IconData settings = Icons.settings_outlined;
  static const IconData reports = Icons.bar_chart_outlined;
  static const IconData staff = Icons.badge_outlined;
  static const IconData admin = Icons.admin_panel_settings_outlined;
  static const IconData help = Icons.help_outline;

  // POS
  static const IconData search = Icons.search_outlined;
  static const IconData refresh = Icons.refresh_outlined;
  static const IconData refunds = Icons.assignment_return_outlined;
  static const IconData wifiOff = Icons.wifi_off_outlined;
  static const IconData sync = Icons.sync_outlined;
  static const IconData drawer = Icons.inventory_2_outlined;
  static const IconData drawerOpen = Icons.lock_open_outlined;
  static const IconData personOff = Icons.person_off_outlined;
  static const IconData addCircle = Icons.add_circle_outline;
  static const IconData removeCircle = Icons.remove_circle_outline;
  static const IconData close = Icons.close_outlined;
  static const IconData shoppingCart = Icons.shopping_cart_outlined;
  static const IconData bolt = Icons.bolt_outlined;
  static const IconData peopleAlt = Icons.people_alt_outlined;

  // Commerce
  static const IconData factory = Icons.factory_outlined;
  static const IconData ledger = Icons.menu_book_outlined;
  static const IconData invoice = Icons.receipt_outlined;
  static const IconData map = Icons.map_outlined;
  static const IconData localShipping = Icons.local_shipping_outlined;
  static const IconData directionsCar = Icons.directions_car_outlined;
  static const IconData personAdd = Icons.person_add_alt;
  static const IconData payments = Icons.payments_outlined;
  static const IconData creditCard = Icons.credit_card_outlined;
  static const IconData split = Icons.call_split_outlined;
  static const IconData location = Icons.location_on_outlined;
  static const IconData myLocation = Icons.my_location_outlined;

  // System
  static const IconData add = Icons.add;
  static const IconData edit = Icons.edit_outlined;
  static const IconData save = Icons.save_outlined;
  static const IconData image = Icons.image_outlined;
  static const IconData paused = Icons.pause_circle_outline;
  static const IconData error = Icons.error_outline_outlined;
  static const IconData info = Icons.info_outline;
  static const IconData checkCircle = Icons.check_circle_outline;
  static const IconData inbox = Icons.inbox_outlined;
  static const IconData logout = Icons.logout_outlined;
  static const IconData darkMode = Icons.dark_mode_outlined;
  static const IconData lightMode = Icons.light_mode_outlined;
  static const IconData language = Icons.language_outlined;
  static const IconData menu = Icons.menu_outlined;
  static const IconData chevronRight = Icons.chevron_right_outlined;

  // Helper to get consistent size
  static Icon icon(IconData data, {double size = 20, Color? color}) =>
      Icon(data, size: size, color: color);
}
