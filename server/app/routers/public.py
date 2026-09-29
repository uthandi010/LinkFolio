from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_db

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/profiles/{username}", response_model=schemas.PublicProfileResponse)
def get_public_profile(username: str, db: Session = Depends(get_db)) -> schemas.PublicProfileResponse:
    user = db.scalar(select(models.User).where(models.User.username == username.lower()))
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This profile doesn't exist.")

    active_links = [link for link in user.links if link.active]
    return schemas.PublicProfileResponse(
        name=user.name,
        username=user.username,
        bio=user.bio,
        links=[schemas.PublicLinkResponse.model_validate(link) for link in active_links],
    )


@router.get("/links/{link_id}/go")
def click_link(link_id: int, request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    """Records a click, then redirects the visitor to the link's real URL.

    A real <a href> pointing here (rather than straight at the target) is
    what lets the dashboard count clicks at all - the browser follows the
    redirect transparently, so the visitor experience is unaffected.
    """
    link = db.get(models.Link, link_id)
    if link is None or not link.active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This link is no longer available.")

    referrer = request.headers.get("referer")
    db.add(models.Click(link_id=link.id, referrer=referrer))
    db.commit()

    return RedirectResponse(url=link.url, status_code=status.HTTP_302_FOUND)
