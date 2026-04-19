from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import extract, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import CrewMember, RosterEvent


router = APIRouter(prefix="/api/calendar", tags=["calendar"])


@router.get("/month")
def get_calendar_month(year: int = Query(...), month: int = Query(...), db: Session = Depends(get_db)):
    rows = db.execute(
        select(RosterEvent, CrewMember.crew_id)
        .join(CrewMember, CrewMember.id == RosterEvent.crew_member_id)
        .where(extract("year", RosterEvent.start_date_local) == year)
        .where(extract("month", RosterEvent.start_date_local) == month)
    ).all()

    grouped = defaultdict(lambda: defaultdict(set))
    for event, crew_id in rows:
        grouped[event.start_date_local][event.normalized_label].add(crew_id)

    days = []
    for day in sorted(grouped.keys()):
        items = []
        for label in sorted(grouped[day].keys()):
            items.append({"label": label, "crew_ids": sorted(grouped[day][label])})
        days.append({"date": day, "items": items})

    return {"year": year, "month": month, "days": days}


@router.get("/day")
def get_calendar_day(target_date: date = Query(..., alias="date"), db: Session = Depends(get_db)):
    rows = db.execute(
        select(RosterEvent, CrewMember.crew_id)
        .join(CrewMember, CrewMember.id == RosterEvent.crew_member_id)
        .where(RosterEvent.start_date_local == target_date)
    ).all()

    grouped = defaultdict(lambda: {"crew_ids": set(), "events": []})
    for event, crew_id in rows:
        grouped[event.normalized_label]["crew_ids"].add(crew_id)
        grouped[event.normalized_label]["events"].append(
            {
                "crew_id": crew_id,
                "start_at": event.start_at,
                "end_at": event.end_at,
                "summary_raw": event.summary_raw,
            }
        )

    items = []
    for label in sorted(grouped.keys()):
        items.append(
            {
                "label": label,
                "crew_ids": sorted(grouped[label]["crew_ids"]),
                "events": grouped[label]["events"],
            }
        )

    return {"date": target_date, "items": items}
