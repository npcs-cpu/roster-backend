from datetime import datetime
import hashlib
from zoneinfo import ZoneInfo

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import CrewCalendarFeed, CrewMember, RosterEvent
from app.services.feed_fetcher import fetch_feed, normalize_feed_url
from app.services.ics_parser import parse_ics_events
from app.services.normalizer import normalize_event
from app.utils.crypto import encrypt_text
from app.utils.time_window import current_and_next_month_window


JFK_TZ = ZoneInfo("America/New_York")


async def sync_single_crew_feed(db: Session, crew_id: str, feed_url: str):
    normalized_url = normalize_feed_url(feed_url)

    crew = db.execute(select(CrewMember).where(CrewMember.crew_id == crew_id)).scalar_one_or_none()
    if not crew:
        crew = CrewMember(crew_id=crew_id, base_code="JFK", is_active=True)
        db.add(crew)
        db.commit()
        db.refresh(crew)

    feed = db.execute(select(CrewCalendarFeed).where(CrewCalendarFeed.crew_member_id == crew.id)).scalar_one_or_none()

    encrypted = encrypt_text(normalized_url)
    feed_hash = hashlib.sha256(normalized_url.encode()).hexdigest()

    if not feed:
        feed = CrewCalendarFeed(
            crew_member_id=crew.id,
            encrypted_feed_url=encrypted,
            feed_url_hash=feed_hash,
            is_active=True,
        )
        db.add(feed)
        db.commit()
        db.refresh(feed)
    else:
        feed.encrypted_feed_url = encrypted
        feed.feed_url_hash = feed_hash
        feed.updated_at = datetime.utcnow()
        db.commit()

    window_start, window_end = current_and_next_month_window()

    try:
        ics_text, source_hash = await fetch_feed(normalized_url)
        parsed = parse_ics_events(ics_text)
        feed.last_fetched_at = datetime.utcnow()
        feed.last_success_at = datetime.utcnow()
        feed.fetch_error = None
        db.commit()
    except Exception as exc:
        feed.last_fetched_at = datetime.utcnow()
        feed.fetch_error = str(exc)
        db.commit()
        raise

    filtered = []
    for event in parsed:
        start_local = event["start_at"].astimezone(JFK_TZ)
        if window_start <= start_local <= window_end:
            filtered.append(event)

    db.execute(
        delete(RosterEvent).where(
            RosterEvent.crew_member_id == crew.id,
            RosterEvent.start_date_local >= window_start.date(),
            RosterEvent.start_date_local <= window_end.date(),
        )
    )
    db.commit()

    saved = 0
    for event in filtered:
        normalized = normalize_event(event)
        start_local = event["start_at"].astimezone(JFK_TZ)
        end_local = event["end_at"].astimezone(JFK_TZ)

        row = RosterEvent(
            crew_member_id=crew.id,
            external_uid=event["uid"] or f"generated-{saved}",
            start_at=event["start_at"],
            end_at=event["end_at"],
            start_date_local=start_local.date(),
            end_date_local=end_local.date(),
            summary_raw=normalized["summary_raw"],
            activity_code=normalized["activity_code"],
            activity_type=normalized["activity_type"],
            flight_number=normalized["flight_number"],
            origin=normalized["origin"],
            destination=normalized["destination"],
            hotel_city=normalized["hotel_city"],
            normalized_label=normalized["normalized_label"],
            source_hash=source_hash,
        )
        db.add(row)
        saved += 1

    db.commit()

    return {
        "crew_id": crew_id,
        "fetched": True,
        "events_parsed": len(filtered),
        "events_saved": saved,
        "window": {
            "from": str(window_start.date()),
            "to": str(window_end.date()),
        },
    }
