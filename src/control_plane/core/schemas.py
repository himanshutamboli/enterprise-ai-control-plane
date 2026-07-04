"""Request/response schemas for the core API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from control_plane.core.rbac import Role


class OrgOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    slug: str
    created_at: datetime


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    name: str
    role: str
    created_at: datetime


class UserCreateOut(UserOut):
    """Includes the API key — returned only once, at creation time."""

    api_key: str


class OrgCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    owner_email: str = Field(min_length=3, max_length=255)
    owner_name: str = Field(min_length=1, max_length=200)


class OrgCreateOut(BaseModel):
    org: OrgOut
    owner: UserCreateOut


class UserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    name: str = Field(min_length=1, max_length=200)
    role: Role = Role.MEMBER
