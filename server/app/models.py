from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    bio: Mapped[str | None] = mapped_column(String(280), default=None)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    links: Mapped[list["Link"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan", order_by="Link.position"
    )


class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(120))
    url: Mapped[str] = mapped_column(String(2048))
    position: Mapped[int] = mapped_column(default=0)
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    owner: Mapped["User"] = relationship(back_populates="links")
    clicks: Mapped[list["Click"]] = relationship(back_populates="link", cascade="all, delete-orphan")


class Click(Base):
    __tablename__ = "clicks"
    __table_args__ = (Index("ix_clicks_link_id_clicked_at", "link_id", "clicked_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    link_id: Mapped[int] = mapped_column(ForeignKey("links.id", ondelete="CASCADE"), index=True)
    clicked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    # Best-effort, low-cardinality context for the dashboard - never an IP
    # address or anything else that could identify a visitor.
    referrer: Mapped[str | None] = mapped_column(Text, default=None)

    link: Mapped["Link"] = relationship(back_populates="clicks")
