library;


class AuditLogEntry {
  final int id;
  final int? userId;
  final String action;
  final String? resourceType;
  final int? resourceId;
  final String? detailsJson;
  final String? ipAddress;
  final String? requestId;
  final String? createdAt;

  const AuditLogEntry({
    required this.id,
    this.userId,
    required this.action,
    this.resourceType,
    this.resourceId,
    this.detailsJson,
    this.ipAddress,
    this.requestId,
    this.createdAt,
  });

  factory AuditLogEntry.fromJson(Map<String, dynamic> json) => AuditLogEntry(
    id: json['id'] as int,
    userId: json['user_id'] as int?,
    action: json['action'] as String,
    resourceType: json['resource_type'] as String?,
    resourceId: json['resource_id'] as int?,
    detailsJson: json['details_json'] as String?,
    ipAddress: json['ip_address'] as String?,
    requestId: json['request_id'] as String?,
    createdAt: json['created_at'] as String?,
  );
}
