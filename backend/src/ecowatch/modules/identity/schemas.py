"""Pydantic boundary schemas for identity, auth, organisations, and memberships."""

import uuid
from datetime import datetime

from pydantic import Field, field_validator

from ecowatch.core.schemas import CamelModel
from ecowatch.modules.identity.permissions import Role, SystemRole


class LoginRequest(CamelModel):
    """Credentials payload for local token issuance."""

    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class MembershipResponse(CamelModel):
    """Public representation of an organisation membership."""

    id: uuid.UUID
    userId: uuid.UUID
    organisationId: uuid.UUID
    role: Role
    isActive: bool
    createdAt: datetime


class UserResponse(CamelModel):
    """Public representation of a user account (never includes passwordHash)."""

    id: uuid.UUID
    email: str
    displayName: str
    systemRole: SystemRole | None = None
    isActive: bool
    createdAt: datetime
    updatedAt: datetime


class AuthMeResponse(UserResponse):
    """Authenticated user profile including active organisation memberships."""

    memberships: list[MembershipResponse] = Field(default_factory=list)


class LoginResponse(CamelModel):
    """Bearer access token response returned on successful login."""

    accessToken: str
    tokenType: str = "bearer"
    user: UserResponse


class CreateUserRequest(CamelModel):
    """System-admin payload to create a user account."""

    email: str = Field(min_length=3, max_length=255)
    displayName: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)
    systemRole: SystemRole | None = None
    isActive: bool = True

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized or " " in normalized:
            raise ValueError("Invalid email address format")
        return normalized


class CreateOrganisationRequest(CamelModel):
    """System-admin payload to create a tenant organisation."""

    name: str = Field(min_length=2, max_length=200)
    orgType: str = Field(min_length=2, max_length=64)
    isActive: bool = True


class OrganisationResponse(CamelModel):
    """Public representation of an organisation."""

    id: uuid.UUID
    name: str
    orgType: str
    isActive: bool
    createdAt: datetime
    updatedAt: datetime


class AssignMembershipRequest(CamelModel):
    """Payload to assign or update a user's role within an organisation."""

    userId: uuid.UUID
    role: Role
    isActive: bool = True
    reason: str | None = Field(default=None, max_length=500)
