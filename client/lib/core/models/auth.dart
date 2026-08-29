import 'package:freezed_annotation/freezed_annotation.dart';

import 'converters.dart';

part 'auth.freezed.dart';
part 'auth.g.dart';

@freezed
abstract class PermissionInfo with _$PermissionInfo {
  const factory PermissionInfo({
    required int id,
    required String code,
    String? description,
  }) = _PermissionInfo;

  factory PermissionInfo.fromJson(Map<String, dynamic> json) =>
      _$PermissionInfoFromJson(json);
}

@freezed
abstract class RoleInfo with _$RoleInfo {
  const factory RoleInfo({
    required int id,
    required String name,
    String? description,
    @Default(false) bool isSystem,
    @JsonKey(fromJson: permsFromJson, toJson: permsToJson)
    @Default([])
    List<String> permissions,
  }) = _RoleInfo;

  factory RoleInfo.fromJson(Map<String, dynamic> json) =>
      _$RoleInfoFromJson(json);
}

@freezed
abstract class UserProfile with _$UserProfile {
  const factory UserProfile({
    required int id,
    required String email,
    String? fullName,
    @Default(true) bool isActive,
    @Default(false) bool isSuperuser,
    int? tenantId,
    @JsonKey(fromJson: rolesFromJson, toJson: rolesToJson) @Default([]) List<String> roles,
  }) = _UserProfile;

  factory UserProfile.fromJson(Map<String, dynamic> json) =>
      _$UserProfileFromJson(json);
}

@freezed
abstract class TokenResponse with _$TokenResponse {
  const factory TokenResponse({
    required String accessToken,
    required String refreshToken,
    @Default('bearer') String tokenType,
  }) = _TokenResponse;

  factory TokenResponse.fromJson(Map<String, dynamic> json) =>
      _$TokenResponseFromJson(json);
}

@freezed
abstract class User with _$User {
  const factory User({
    required int id,
    required String email,
    String? fullName,
    @Default(true) bool isActive,
    @Default(false) bool isSuperuser,
  }) = _User;

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
}
