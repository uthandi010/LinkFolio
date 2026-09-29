import re

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

USERNAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def normalize_username(value: str) -> str:
    normalized = value.strip().lower()
    if not USERNAME_PATTERN.match(normalized):
        raise ValueError("username can only contain lowercase letters, numbers, and single hyphens")
    return normalized


# ----- Auth -----
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        return normalize_username(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("password must be at least 8 characters")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    token: str
    user_id: int
    name: str
    email: str
    username: str


# ----- Me / profile -----
class MeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    username: str
    bio: str | None


class UpdateMeRequest(BaseModel):
    name: str | None = None
    bio: str | None = None
    username: str | None = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str | None) -> str | None:
        return normalize_username(value) if value is not None else value


# ----- Links -----
class LinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    url: str
    position: int
    active: bool


class CreateLinkRequest(BaseModel):
    title: str
    url: str


class UpdateLinkRequest(BaseModel):
    title: str | None = None
    url: str | None = None
    active: bool | None = None


class ReorderLinksRequest(BaseModel):
    link_ids: list[int]


# ----- Public profile -----
class PublicLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    url: str


class PublicProfileResponse(BaseModel):
    name: str
    username: str
    bio: str | None
    links: list[PublicLinkResponse]


# ----- Analytics -----
class LinkClickCount(BaseModel):
    link_id: int
    title: str
    clicks: int


class ClicksByDay(BaseModel):
    date: str
    clicks: int


class AnalyticsSummary(BaseModel):
    total_clicks: int
    total_links: int
    clicks_by_link: list[LinkClickCount]
    clicks_by_day: list[ClicksByDay]


class ErrorResponse(BaseModel):
    message: str
