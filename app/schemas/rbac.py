from typing import List, Optional

from pydantic import BaseModel, Field


class PermissionBase(BaseModel):
    code: str
    description: Optional[str] = None


class Permission(PermissionBase):
    id: int

    model_config = {"from_attributes": True}


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    permission_codes: List[str] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permission_codes: Optional[List[str]] = None


class Role(RoleBase):
    id: int
    is_system: bool
    permissions: List[Permission] = []

    model_config = {"from_attributes": True}


class UserRoleAssign(BaseModel):
    role_ids: List[int] = Field(default_factory=list)


class UserRolesResponse(BaseModel):
    user_id: int
    roles: List[Role]


class UserPermissionsResponse(BaseModel):
    user_id: int
    permissions: List[str]
