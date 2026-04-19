from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class CrewMember(Base):
    __tablename__ = "crew_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    crew_id: Mapped[str] = mapped_column(String(5), unique=True, nullable=False)
    base_code: Mapped[str] = mapped_column(String(3), nullable=False, default="JFK")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    feeds = relationship("CrewCalendarFeed", back_populates="crew_member", cascade="all, delete-orphan")
    events = relationship("RosterEvent", back_populates="crew_member", cascade="all, delete-orphan")


class CrewCalendarFeed(Base):
    __tablename__ = "crew_calendar_feeds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    crew_member_id: Mapped[int] = mapped_column(ForeignKey("crew_members.id", ondelete="CASCADE"), nullable=False)
    encrypted_feed_url: Mapped[str] = mapped_column(Text, nullable=False)
    feed_url_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fetch_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    crew_member = relationship("CrewMember", back_populates="feeds")


class RosterEvent(Base):
    __tablename__ = "roster_events"
    __table_args__ = (
        UniqueConstraint("crew_member_id", "external_uid", "start_at", name="uq_roster_event_unique"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    crew_member_id: Mapped[int] = mapped_column(ForeignKey("crew_members.id", ondelete="CASCADE"), nullable=False)
    external_uid: Mapped[str] = mapped_column(Text, nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    start_date_local: Mapped[date] = mapped_column(Date, nullable=False)
    end_date_local: Mapped[date] = mapped_column(Date, nullable=False)
    summary_raw: Mapped[str] = mapped_column(Text, nullable=False)
    activity_code: Mapped[str] = mapped_column(String(32), nullable=False)
    activity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    flight_number: Mapped[str | None] = mapped_column(String(16), nullable=True)
    origin: Mapped[str | None] = mapped_column(String(3), nullable=True)
    destination: Mapped[str | None] = mapped_column(String(3), nullable=True)
    hotel_city: Mapped[str | None] = mapped_column(String(8), nullable=True)
    normalized_label: Mapped[str] = mapped_column(Text, nullable=False)
    source_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    updated_from_feed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    crew_member = relationship("CrewMember", back_populates="events")
