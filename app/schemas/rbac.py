from pydantic import BaseModel, Field


class PermissionBase(BaseModel):
    code: str
    description: str | None = None


class Permission(PermissionBase):
    id: int

    model_config = {"from_attributes": True}


class RoleBase(BaseModel):
    name: str
    description: str | None = None


class RoleCreate(RoleBase):
    permission_codes: list[str] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    permission_codes: list[str] | None = None


class Role(RoleBase):
    id: int
    is_system: bool
    permissions: list[Permission] = []

    model_config = {"from_attributes": True}


class UserRoleAssign(BaseModel):
    role_ids: list[int] = Field(default_factory=list)


class UserRolesResponse(BaseModel):
    user_id: int
    roles: list[Role]


class UserPermissionsResponse(BaseModel):
    user_id: int
    permissions: list[str]
