import hashlib
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import CrewCalendarFeed, CrewMember, RosterEvent
from app.services.feed_fetcher import normalize_feed_url
from app.services.sync_service import sync_single_crew_feed
from app.utils.crypto import decrypt_text, encrypt_text


router = APIRouter(prefix="/api/admin", tags=["admin"])


def require_admin(x_admin_token: Optional[str] = Header(default=None)):
    if settings.admin_api_token and x_admin_token != settings.admin_api_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin token")


# ── Schemas ──────────────────────────────────────────────────────────────────

class AddCrewRequest(BaseModel):
    crew_id: str
    feed_url: str
    display_name: Optional[str] = None


class UpdateCrewRequest(BaseModel):
    is_active: Optional[bool] = None
    display_name: Optional[str] = None


class SyncFeedRequest(BaseModel):
    feed_url: str


# ── Crew management ───────────────────────────────────────────────────────────

@router.get("/crew", dependencies=[Depends(require_admin)])
def list_crew(db: Session = Depends(get_db)):
    rows = db.execute(select(CrewMember)).scalars().all()
    result = []
    for crew in rows:
        feed = db.execute(
            select(CrewCalendarFeed).where(CrewCalendarFeed.crew_member_id == crew.id)
        ).scalar_one_or_none()

        result.append({
            "id": crew.id,
            "crew_id": crew.crew_id,
            "base_code": crew.base_code,
            "display_name": getattr(crew, "display_name", None),
            "is_active": crew.is_active,
            "feed": {
                "is_active": feed.is_active if feed else None,
                "last_fetched_at": feed.last_fetched_at if feed else None,
                "last_success_at": feed.last_success_at if feed else None,
                "fetch_error": feed.fetch_error if feed else None,
                # Mask URL — show only last 10 chars
                "feed_url_preview": ("…" + decrypt_text(feed.encrypted_feed_url)[-10:]) if feed else None,
            } if feed else None,
        })
    return result


@router.post("/crew", dependencies=[Depends(require_admin)])
async def add_crew(payload: AddCrewRequest, db: Session = Depends(get_db)):
    crew_id = payload.crew_id.strip()
    if not crew_id or len(crew_id) > 5:
        raise HTTPException(400, "crew_id must be 1-5 characters")

    existing = db.execute(select(CrewMember).where(CrewMember.crew_id == crew_id)).scalar_one_or_none()
    if existing:
        raise HTTPException(409, f"Crew ID {crew_id} already exists")

    normalized_url = normalize_feed_url(payload.feed_url)
    url_hash = hashlib.sha256(normalized_url.encode()).hexdigest()

    dup_feed = db.execute(
        select(CrewCalendarFeed).where(CrewCalendarFeed.feed_url_hash == url_hash)
    ).scalar_one_or_none()
    if dup_feed:
        raise HTTPException(409, "This feed URL is already registered to another crew member")

    result = await sync_single_crew_feed(db=db, crew_id=crew_id, feed_url=normalized_url)
    return {"message": "Crew member added and feed synced", "sync": result}


@router.patch("/crew/{crew_id}", dependencies=[Depends(require_admin)])
def update_crew(crew_id: str, payload: UpdateCrewRequest, db: Session = Depends(get_db)):
    crew = db.execute(select(CrewMember).where(CrewMember.crew_id == crew_id)).scalar_one_or_none()
    if not crew:
        raise HTTPException(404, "Crew member not found")

    if payload.is_active is not None:
        crew.is_active = payload.is_active
    if payload.display_name is not None:
        if hasattr(crew, "display_name"):
            crew.display_name = payload.display_name
    crew.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Updated", "crew_id": crew_id}


@router.delete("/crew/{crew_id}", dependencies=[Depends(require_admin)])
def delete_crew(crew_id: str, db: Session = Depends(get_db)):
    crew = db.execute(select(CrewMember).where(CrewMember.crew_id == crew_id)).scalar_one_or_none()
    if not crew:
        raise HTTPException(404, "Crew member not found")
    db.delete(crew)
    db.commit()
    return {"message": "Deleted", "crew_id": crew_id}


# ── Sync ──────────────────────────────────────────────────────────────────────

@router.post("/crew/{crew_id}/sync", dependencies=[Depends(require_admin)])
async def sync_crew_feed(crew_id: str, payload: SyncFeedRequest, db: Session = Depends(get_db)):
    return await sync_single_crew_feed(db=db, crew_id=crew_id, feed_url=payload.feed_url)


@router.post("/sync/all", dependencies=[Depends(require_admin)])
async def sync_all_feeds(db: Session = Depends(get_db)):
    """Trigger sync for all active feeds."""
    from app.utils.crypto import decrypt_text

    feeds = db.execute(
        select(CrewCalendarFeed, CrewMember.crew_id)
        .join(CrewMember, CrewMember.id == CrewCalendarFeed.crew_member_id)
        .where(CrewCalendarFeed.is_active == True)
        .where(CrewMember.is_active == True)
    ).all()

    results = []
    for feed, crew_id in feeds:
        try:
            url = decrypt_text(feed.encrypted_feed_url)
            r = await sync_single_crew_feed(db=db, crew_id=crew_id, feed_url=url)
            results.append({"crew_id": crew_id, "status": "ok", **r})
        except Exception as e:
            results.append({"crew_id": crew_id, "status": "error", "error": str(e)})

    return {"total": len(results), "results": results}


@router.get("/feeds", dependencies=[Depends(require_admin)])
def list_feeds(db: Session = Depends(get_db)):
    rows = db.execute(
        select(CrewCalendarFeed, CrewMember.crew_id)
        .join(CrewMember, CrewMember.id == CrewCalendarFeed.crew_member_id)
    ).all()

    return [
        {
            "crew_id": crew_id,
            "is_active": f.is_active,
            "last_fetched_at": f.last_fetched_at,
            "last_success_at": f.last_success_at,
            "fetch_error": f.fetch_error,
            "feed_url_preview": "…" + decrypt_text(f.encrypted_feed_url)[-10:],
        }
        for f, crew_id in rows
    ]


@router.get("/stats", dependencies=[Depends(require_admin)])
def get_stats(db: Session = Depends(get_db)):
    total_crew = db.execute(select(CrewMember)).scalars().all()
    active_crew = [c for c in total_crew if c.is_active]
    total_events = db.execute(select(RosterEvent)).scalars().all()

    return {
        "total_crew": len(total_crew),
        "active_crew": len(active_crew),
        "total_events": len(total_events),
    }
