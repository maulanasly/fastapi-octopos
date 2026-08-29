library;

double doubleFromJson(Object? json) => (json as num?)?.toDouble() ?? 0;

double? nullableDoubleFromJson(Object? json) => (json as num?)?.toDouble();

int intFromJson(Object? json) => (json as num?)?.toInt() ?? 0;

int? nullableIntFromJson(Object? json) => (json as num?)?.toInt();

/// Role permissions come as `List<Map<String, dynamic>>` with `code`; unwrap to `List<String>`.
List<String> permsFromJson(Object? json) {
  final list = json as List? ?? const [];
  return list
      .map((e) => (e as Map<String, dynamic>)['code'] as String? ?? '')
      .where((s) => s.isNotEmpty)
      .toList();
}

Object permsToJson(List<String> perms) =>
    perms.map((c) => {'code': c}).toList();

List<String> rolesFromJson(Object? json) {
  final list = json as List? ?? const [];
  return list
      .map((e) => (e as Map<String, dynamic>)['name'] as String? ?? '')
      .where((s) => s.isNotEmpty)
      .toList();
}

Object rolesToJson(List<String> roles) =>
    roles.map((n) => {'name': n}).toList();
