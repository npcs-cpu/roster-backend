from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from icalendar import Calendar


JFK_TZ = ZoneInfo("America/New_York")



def ensure_datetime(value) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=JFK_TZ)
        return value
    if isinstance(value, date):
        return datetime.combine(value, time.min, tzinfo=JFK_TZ)
    raise ValueError("Unsupported ICS date type")



def parse_ics_events(ics_text: str) -> list[dict]:
    calendar = Calendar.from_ical(ics_text)
    events: list[dict] = []

    for component in calendar.walk():
        if component.name != "VEVENT":
            continue

        uid = str(component.get("UID", "")).strip()
        summary = str(component.get("SUMMARY", "")).strip()
        description = str(component.get("DESCRIPTION", "")).strip()
        location = str(component.get("LOCATION", "")).strip()

        dtstart = ensure_datetime(component.decoded("DTSTART"))
        dtend = ensure_datetime(component.decoded("DTEND"))

        events.append(
            {
                "uid": uid,
                "summary": summary,
                "description": description,
                "location": location,
                "start_at": dtstart,
                "end_at": dtend,
            }
        )

    return events
