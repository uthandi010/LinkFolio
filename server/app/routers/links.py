from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, insert, select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_current_user, get_db

router = APIRouter(prefix="/api/links", tags=["links"])


def _get_owned_link(db: Session, current_user: models.User, link_id: int) -> models.Link:
    link = db.get(models.Link, link_id)
    if link is None or link.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Link not found.")
    return link


@router.get("", response_model=list[schemas.LinkResponse])
def list_links(
    current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[models.Link]:
    stmt = select(models.Link).where(models.Link.user_id == current_user.id).order_by(models.Link.position)
    return list(db.scalars(stmt))


@router.post("", response_model=schemas.LinkResponse, status_code=status.HTTP_201_CREATED)
def create_link(
    payload: schemas.CreateLinkRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.Link:
    if not payload.title.strip():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Title is required.")

    # The next position is computed inside the INSERT itself, so the
    # read-max-then-write race between concurrent requests can't hand two
    # links the same position.
    next_position = (
        select(func.coalesce(func.max(models.Link.position) + 1, 0))
        .where(models.Link.user_id == current_user.id)
        .scalar_subquery()
    )
    link_id = db.execute(
        insert(models.Link)
        .values(
            user_id=current_user.id,
            title=payload.title.strip(),
            url=payload.url,
            position=next_position,
        )
        .returning(models.Link.id)
    ).scalar_one()
    db.commit()
    return db.get(models.Link, link_id)


@router.patch("/{link_id}", response_model=schemas.LinkResponse)
def update_link(
    link_id: int,
    payload: schemas.UpdateLinkRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.Link:
    link = _get_owned_link(db, current_user, link_id)

    if payload.title is not None:
        if not payload.title.strip():
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Title cannot be blank.")
        link.title = payload.title.strip()
    if payload.url is not None:
        link.url = payload.url
    if payload.active is not None:
        link.active = payload.active

    db.commit()
    db.refresh(link)
    return link


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_link(
    link_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    link = _get_owned_link(db, current_user, link_id)
    db.delete(link)
    db.commit()


@router.post("/reorder", response_model=list[schemas.LinkResponse])
def reorder_links(
    payload: schemas.ReorderLinksRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[models.Link]:
    my_links = {
        link.id: link
        for link in db.scalars(select(models.Link).where(models.Link.user_id == current_user.id))
    }

    if set(payload.link_ids) != set(my_links.keys()):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "link_ids must contain exactly your current links, each exactly once.",
        )

    for position, link_id in enumerate(payload.link_ids):
        my_links[link_id].position = position

    db.commit()
    return sorted(my_links.values(), key=lambda link: link.position)
