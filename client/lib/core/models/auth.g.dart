// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'auth.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_PermissionInfo _$PermissionInfoFromJson(Map<String, dynamic> json) =>
    $checkedCreate('_PermissionInfo', json, ($checkedConvert) {
      final val = _PermissionInfo(
        id: $checkedConvert('id', (v) => (v as num).toInt()),
        code: $checkedConvert('code', (v) => v as String),
        description: $checkedConvert('description', (v) => v as String?),
      );
      return val;
    });

Map<String, dynamic> _$PermissionInfoToJson(_PermissionInfo instance) =>
    <String, dynamic>{
      'id': instance.id,
      'code': instance.code,
      'description': ?instance.description,
    };

_RoleInfo _$RoleInfoFromJson(Map<String, dynamic> json) =>
    $checkedCreate('_RoleInfo', json, ($checkedConvert) {
      final val = _RoleInfo(
        id: $checkedConvert('id', (v) => (v as num).toInt()),
        name: $checkedConvert('name', (v) => v as String),
        description: $checkedConvert('description', (v) => v as String?),
        isSystem: $checkedConvert('is_system', (v) => v as bool? ?? false),
        permissions: $checkedConvert(
          'permissions',
          (v) => v == null ? const [] : permsFromJson(v),
        ),
      );
      return val;
    }, fieldKeyMap: const {'isSystem': 'is_system'});

Map<String, dynamic> _$RoleInfoToJson(_RoleInfo instance) => <String, dynamic>{
  'id': instance.id,
  'name': instance.name,
  'description': ?instance.description,
  'is_system': instance.isSystem,
  'permissions': permsToJson(instance.permissions),
};

_UserProfile _$UserProfileFromJson(Map<String, dynamic> json) => $checkedCreate(
  '_UserProfile',
  json,
  ($checkedConvert) {
    final val = _UserProfile(
      id: $checkedConvert('id', (v) => (v as num).toInt()),
      email: $checkedConvert('email', (v) => v as String),
      fullName: $checkedConvert('full_name', (v) => v as String?),
      isActive: $checkedConvert('is_active', (v) => v as bool? ?? true),
      isSuperuser: $checkedConvert('is_superuser', (v) => v as bool? ?? false),
      tenantId: $checkedConvert('tenant_id', (v) => (v as num?)?.toInt()),
      roles: $checkedConvert(
        'roles',
        (v) => v == null ? const [] : rolesFromJson(v),
      ),
    );
    return val;
  },
  fieldKeyMap: const {
    'fullName': 'full_name',
    'isActive': 'is_active',
    'isSuperuser': 'is_superuser',
    'tenantId': 'tenant_id',
  },
);

Map<String, dynamic> _$UserProfileToJson(_UserProfile instance) =>
    <String, dynamic>{
      'id': instance.id,
      'email': instance.email,
      'full_name': ?instance.fullName,
      'is_active': instance.isActive,
      'is_superuser': instance.isSuperuser,
      'tenant_id': ?instance.tenantId,
      'roles': rolesToJson(instance.roles),
    };

_TokenResponse _$TokenResponseFromJson(Map<String, dynamic> json) =>
    $checkedCreate(
      '_TokenResponse',
      json,
      ($checkedConvert) {
        final val = _TokenResponse(
          accessToken: $checkedConvert('access_token', (v) => v as String),
          refreshToken: $checkedConvert('refresh_token', (v) => v as String),
          tokenType: $checkedConvert(
            'token_type',
            (v) => v as String? ?? 'bearer',
          ),
        );
        return val;
      },
      fieldKeyMap: const {
        'accessToken': 'access_token',
        'refreshToken': 'refresh_token',
        'tokenType': 'token_type',
      },
    );

Map<String, dynamic> _$TokenResponseToJson(_TokenResponse instance) =>
    <String, dynamic>{
      'access_token': instance.accessToken,
      'refresh_token': instance.refreshToken,
      'token_type': instance.tokenType,
    };

_User _$UserFromJson(Map<String, dynamic> json) => $checkedCreate(
  '_User',
  json,
  ($checkedConvert) {
    final val = _User(
      id: $checkedConvert('id', (v) => (v as num).toInt()),
      email: $checkedConvert('email', (v) => v as String),
      fullName: $checkedConvert('full_name', (v) => v as String?),
      isActive: $checkedConvert('is_active', (v) => v as bool? ?? true),
      isSuperuser: $checkedConvert('is_superuser', (v) => v as bool? ?? false),
    );
    return val;
  },
  fieldKeyMap: const {
    'fullName': 'full_name',
    'isActive': 'is_active',
    'isSuperuser': 'is_superuser',
  },
);

Map<String, dynamic> _$UserToJson(_User instance) => <String, dynamic>{
  'id': instance.id,
  'email': instance.email,
  'full_name': ?instance.fullName,
  'is_active': instance.isActive,
  'is_superuser': instance.isSuperuser,
};
