from datetime import date, datetime

from pydantic import BaseModel


class SyncFeedRequest(BaseModel):
    feed_url: str


class SyncFeedResponse(BaseModel):
    crew_id: str
    fetched: bool
    events_parsed: int
    events_saved: int
    window: dict


class CalendarItem(BaseModel):
    label: str
    crew_ids: list[str]


class CalendarDayResponse(BaseModel):
    date: date
    items: list[CalendarItem]


class CalendarMonthResponse(BaseModel):
    year: int
    month: int
    days: list[CalendarDayResponse]


class CalendarEventDetail(BaseModel):
    crew_id: str
    start_at: datetime
    end_at: datetime
    summary_raw: str


class CalendarDetailItem(BaseModel):
    label: str
    crew_ids: list[str]
    events: list[CalendarEventDetail]


class DayDetailResponse(BaseModel):
    date: date
    items: list[CalendarDetailItem]
