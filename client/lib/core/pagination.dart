library;

/// Simple pagination abstraction to avoid hardcoded `limit: 500` etc.
/// Mirrors backend `limit`/`offset` query params.
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
    if (offset > 0) 'offset': offset,
  };

  PaginationParams copyWith({int? limit, int? offset}) => PaginationParams(
    limit: limit ?? this.limit,
    offset: offset ?? this.offset,
  );
}
