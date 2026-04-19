from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


JFK_TZ = ZoneInfo("America/New_York")



def current_and_next_month_window(now: datetime | None = None):
    now = now.astimezone(JFK_TZ) if now else datetime.now(JFK_TZ)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if start.month == 12:
        next_month = start.replace(year=start.year + 1, month=1)
    else:
        next_month = start.replace(month=start.month + 1)

    if next_month.month == 12:
        month_after = next_month.replace(year=next_month.year + 1, month=1)
    else:
        month_after = next_month.replace(month=next_month.month + 1)

    end = month_after - timedelta(microseconds=1)
    return start, end
