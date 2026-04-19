from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import SyncFeedRequest, SyncFeedResponse
from app.services.sync_service import sync_single_crew_feed


router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/crew/{crew_id}/sync", response_model=SyncFeedResponse)
async def sync_crew_feed(crew_id: str, payload: SyncFeedRequest, db: Session = Depends(get_db)):
    return await sync_single_crew_feed(db=db, crew_id=crew_id, feed_url=payload.feed_url)
