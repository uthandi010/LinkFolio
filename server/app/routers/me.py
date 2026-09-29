from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_current_user, get_db

router = APIRouter(prefix="/api/me", tags=["me"])


@router.get("", response_model=schemas.MeResponse)
def get_me(current_user: models.User = Depends(get_current_user)) -> models.User:
    return current_user


@router.patch("", response_model=schemas.MeResponse)
def update_me(
    payload: schemas.UpdateMeRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.User:
    if payload.username is not None and payload.username != current_user.username:
        taken = db.scalar(
            select(models.User).where(
                models.User.username == payload.username, models.User.id != current_user.id
            )
        )
        if taken is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "That username is already taken.")
        current_user.username = payload.username

    if payload.name is not None:
        current_user.name = payload.name.strip()
    if payload.bio is not None:
        current_user.bio = payload.bio.strip() or None

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "That username is already taken.")

    db.refresh(current_user)
    return current_user
