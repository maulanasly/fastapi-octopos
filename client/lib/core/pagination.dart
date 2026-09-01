library;

/// Simple pagination abstraction to avoid hardcoded `limit: 500` etc.
/// Mirrors backend `limit`/`skip` query params (backend uses `skip`, we keep
/// `offset` as the Dart field name for familiarity).
class PaginationParams {
  final int limit;
  final int offset;

  const PaginationParams({
    this.limit = 50,
    this.offset = 0,
  })  : assert(limit > 0 && limit <= 500, 'limit must be 1..500'),
        assert(offset >= 0, 'offset must be >=0');

  static const catalog = PaginationParams(limit: 500);
  static const recentOrders = PaginationParams(limit: 50);
  static const inventory = PaginationParams(limit: 100);
  static const purchasing = PaginationParams(limit: 100);

  Map<String, dynamic> toQuery() => {
    'limit': limit,
    // Backend expects `skip`; also send `offset` for forward compat.
    if (offset > 0) 'skip': offset,
    if (offset > 0) 'offset': offset,
  };

  PaginationParams copyWith({int? limit, int? offset}) => PaginationParams(
    limit: limit ?? this.limit,
    offset: offset ?? this.offset,
  );
}
