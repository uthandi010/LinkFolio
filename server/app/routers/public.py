from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_db
from ..ratelimit import client_ip, limiter, rate_limit

router = APIRouter(prefix="/api/public", tags=["public"])

MAX_REFERRER_LENGTH = 512
CLICK_DEDUPE_WINDOW_SECONDS = 10


def _is_safe_url(url: str) -> bool:
    try:
        schemas.validate_http_url(url)
    except ValueError:
        return False
    return True


@router.get("/profiles/{username}", response_model=schemas.PublicProfileResponse)
def get_public_profile(username: str, db: Session = Depends(get_db)) -> schemas.PublicProfileResponse:
    user = db.scalar(select(models.User).where(models.User.username == username.lower()))
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This profile doesn't exist.")

    active_links = [link for link in user.links if link.active and _is_safe_url(link.url)]
    return schemas.PublicProfileResponse(
        name=user.name,
        username=user.username,
        bio=user.bio,
        links=[schemas.PublicLinkResponse.model_validate(link) for link in active_links],
    )


@router.get(
    "/links/{link_id}/go",
    dependencies=[Depends(rate_limit("go", limit=60, window_seconds=60))],
)
def click_link(link_id: int, request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    """Records a click, then redirects the visitor to the link's real URL.

    A real <a href> pointing here (rather than straight at the target) is
    what lets the dashboard count clicks at all - the browser follows the
    redirect transparently, so the visitor experience is unaffected.
    """
    link = db.get(models.Link, link_id)
    # Never redirect to anything but http(s), even if a bad URL predates validation.
    if link is None or not link.active or not _is_safe_url(link.url):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This link is no longer available.")

    # Repeat clicks from the same visitor on the same link within a short
    # window are redirected but not counted again.
    if limiter.first_seen((client_ip(request), link.id), CLICK_DEDUPE_WINDOW_SECONDS):
        referrer = (request.headers.get("referer") or "")[:MAX_REFERRER_LENGTH] or None
        db.add(models.Click(link_id=link.id, referrer=referrer))
        db.commit()

    return RedirectResponse(url=link.url, status_code=status.HTTP_302_FOUND)
