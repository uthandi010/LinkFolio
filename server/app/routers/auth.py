from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_db
from ..ratelimit import rate_limit
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _auth_response(user: models.User) -> schemas.AuthResponse:
    return schemas.AuthResponse(
        token=create_access_token(user.id),
        user_id=user.id,
        name=user.name,
        email=user.email,
        username=user.username,
    )


@router.post(
    "/register",
    response_model=schemas.AuthResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("register", limit=5, window_seconds=60))],
)
def register(payload: schemas.RegisterRequest, db: Session = Depends(get_db)) -> schemas.AuthResponse:
    email = payload.email.lower()

    existing_email = db.scalar(select(models.User).where(models.User.email == email))
    if existing_email is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with that email already exists.")

    existing_username = db.scalar(select(models.User).where(models.User.username == payload.username))
    if existing_username is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "That username is already taken.")

    user = models.User(
        name=payload.name.strip(),
        email=email,
        username=payload.username,
        password_hash=hash_password(payload.password),
    )

    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "That email or username is already taken.")

    db.refresh(user)
    return _auth_response(user)


@router.post(
    "/login",
    response_model=schemas.AuthResponse,
    dependencies=[Depends(rate_limit("login", limit=10, window_seconds=60))],
)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)) -> schemas.AuthResponse:
    user = db.scalar(select(models.User).where(models.User.email == payload.email.lower()))

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password.")

    return _auth_response(user)
