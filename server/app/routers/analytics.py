from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_current_user, get_db

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

DAYS_OF_HISTORY = 30


def _zero_filled_days(counts_by_date: dict[str, int]) -> list[schemas.ClicksByDay]:
    """Always returns exactly DAYS_OF_HISTORY entries, oldest first, so the
    dashboard chart has a continuous x-axis even for a brand-new account."""
    today = datetime.now(timezone.utc).date()
    return [
        schemas.ClicksByDay(date=day_key, clicks=counts_by_date.get(day_key, 0))
        for day_key in (
            (today - timedelta(days=offset)).isoformat() for offset in range(DAYS_OF_HISTORY - 1, -1, -1)
        )
    ]


@router.get("/summary", response_model=schemas.AnalyticsSummary)
def get_analytics_summary(
    current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> schemas.AnalyticsSummary:
    link_ids = list(db.scalars(select(models.Link.id).where(models.Link.user_id == current_user.id)))
    total_links = len(link_ids)

    if not link_ids:
        return schemas.AnalyticsSummary(
            total_clicks=0, total_links=0, clicks_by_link=[], clicks_by_day=_zero_filled_days({})
        )

    total_clicks = (
        db.scalar(select(func.count(models.Click.id)).where(models.Click.link_id.in_(link_ids))) or 0
    )

    clicks_by_link_rows = db.execute(
        select(models.Link.id, models.Link.title, func.count(models.Click.id))
        .outerjoin(models.Click, models.Click.link_id == models.Link.id)
        .where(models.Link.user_id == current_user.id)
        .group_by(models.Link.id)
        .order_by(func.count(models.Click.id).desc())
    ).all()

    referrer_rows = db.execute(
        select(models.Click.link_id, models.Click.referrer, func.count(models.Click.id))
        .where(models.Click.link_id.in_(link_ids))
        .group_by(models.Click.link_id, models.Click.referrer)
        .order_by(func.count(models.Click.id).desc())
    ).all()
    referrers_by_link: dict[int, list[schemas.ReferrerCount]] = {}
    for link_id, referrer, count in referrer_rows:
        referrers_by_link.setdefault(link_id, []).append(
            schemas.ReferrerCount(referrer=referrer or "(direct)", clicks=count)
        )

    clicks_by_link = [
        schemas.LinkClickCount(
            link_id=row[0], title=row[1], clicks=row[2], referrers=referrers_by_link.get(row[0], [])
        )
        for row in clicks_by_link_rows
    ]

    # Start of the oldest UTC day in the window, matching _zero_filled_days.
    window_start = datetime.now(timezone.utc).date() - timedelta(days=DAYS_OF_HISTORY - 1)
    since = datetime(window_start.year, window_start.month, window_start.day, tzinfo=timezone.utc)
    daily_rows = db.execute(
        select(func.date(models.Click.clicked_at), func.count(models.Click.id))
        .where(models.Click.link_id.in_(link_ids), models.Click.clicked_at >= since)
        .group_by(func.date(models.Click.clicked_at))
    ).all()
    counts_by_date = {row[0]: row[1] for row in daily_rows}

    return schemas.AnalyticsSummary(
        total_clicks=total_clicks,
        total_links=total_links,
        clicks_by_link=clicks_by_link,
        clicks_by_day=_zero_filled_days(counts_by_date),
    )
