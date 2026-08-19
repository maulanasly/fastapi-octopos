/// Shared responsive layout helpers.
library;

import 'package:flutter/material.dart';

/// Dialog width that fits the screen (phones) while staying readable on
/// larger displays.
double dialogWidth(BuildContext context) {
  return (MediaQuery.sizeOf(context).width - 32).clamp(0.0, 420.0);
}
