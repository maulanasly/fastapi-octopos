library;

import 'package:uuid/uuid.dart';

const _uuid = Uuid();

String newIdempotencyKey() => _uuid.v4();

Map<String, dynamic> withIdempotencyKey(
  Map<String, dynamic> body, {
  String? key,
}) => {
  ...body,
  'idempotency_key': ?key,
};

// Backwards compat for existing call sites that used _withKey
Map<String, dynamic> withKey(
  Map<String, dynamic> body, {
  String? key,
}) =>
    withIdempotencyKey(body, key: key);
