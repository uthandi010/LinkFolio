import re
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

USERNAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
USERNAME_MAX_LENGTH = 50
NAME_MAX_LENGTH = 120
TITLE_MAX_LENGTH = 120
BIO_MAX_LENGTH = 280
URL_MAX_LENGTH = 2048

# Usernames that would collide with app routes or look official.
RESERVED_USERNAMES = frozenset(
    {
        "admin", "administrator", "api", "go", "u", "login", "logout", "register", "signup",
        "dashboard", "analytics", "settings", "public", "static", "assets", "health",
        "support", "help", "root", "linkfolio", "www",
    }
)


def normalize_username(value: str) -> str:
    normalized = value.strip().lower()
    if not USERNAME_PATTERN.match(normalized):
        raise ValueError("username can only contain lowercase letters, numbers, and single hyphens")
    if normalized in RESERVED_USERNAMES:
        raise ValueError("that username is reserved")
    return normalized


def validate_http_url(value: str) -> str:
    """Returns the stripped URL if it is a well-formed http(s) URL with a host, else raises ValueError."""
    url = value.strip()
    if not url or len(url) > URL_MAX_LENGTH:
        raise ValueError(f"url must be between 1 and {URL_MAX_LENGTH} characters")
    if any(ch.isspace() or ord(ch) < 32 or ord(ch) == 127 for ch in url):
        raise ValueError("url must not contain whitespace or control characters")
    try:
        parts = urlsplit(url)
        host = parts.hostname
        parts.port  # noqa: B018 - raises ValueError on an invalid port
    except ValueError as exc:
        raise ValueError("url is not valid") from exc
    if parts.scheme.lower() not in ("http", "https"):
        raise ValueError("url must start with http:// or https://")
    if not host:
        raise ValueError("url must include a host")
    return url


# ----- Auth -----
class RegisterRequest(BaseModel):
    name: str = Field(max_length=NAME_MAX_LENGTH)
    email: EmailStr
    username: str = Field(max_length=USERNAME_MAX_LENGTH)
    password: str = Field(max_length=128)

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
    name: str | None = Field(default=None, max_length=NAME_MAX_LENGTH)
    bio: str | None = Field(default=None, max_length=BIO_MAX_LENGTH)
    username: str | None = Field(default=None, max_length=USERNAME_MAX_LENGTH)

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
    title: str = Field(max_length=TITLE_MAX_LENGTH)
    url: str = Field(max_length=URL_MAX_LENGTH)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        return validate_http_url(value)


class UpdateLinkRequest(BaseModel):
    title: str | None = Field(default=None, max_length=TITLE_MAX_LENGTH)
    url: str | None = Field(default=None, max_length=URL_MAX_LENGTH)
    active: bool | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        return validate_http_url(value) if value is not None else value


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
class ReferrerCount(BaseModel):
    referrer: str  # "(direct)" when the click carried no Referer header
    clicks: int


class LinkClickCount(BaseModel):
    link_id: int
    title: str
    clicks: int
    referrers: list[ReferrerCount] = []


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
