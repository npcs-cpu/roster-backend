import re

FLIGHT_RE = re.compile(r"^([A-Z]\d{3,4})\s+([A-Z]{3})-([A-Z]{3})$")
HOTEL_RE = re.compile(r"^HOTEL\s*\(([A-Z]{3})\)$", re.IGNORECASE)
SBY_RE = re.compile(r"^SBY\s*(\d+)$", re.IGNORECASE)
RSV_RE = re.compile(r"^RSV\s*(\d+)$", re.IGNORECASE)



def normalize_event(event: dict) -> dict:
    summary = (event.get("summary") or "").strip()
    cleaned = re.sub(r"\s+", " ", summary).strip()

    base = {
        "summary_raw": cleaned,
        "flight_number": None,
        "origin": None,
        "destination": None,
        "hotel_city": None,
    }

    match = FLIGHT_RE.match(cleaned)
    if match:
        flight, origin, destination = match.groups()
        return {
            **base,
            "activity_type": "flight",
            "activity_code": flight,
            "flight_number": flight,
            "origin": origin,
            "destination": destination,
            "normalized_label": f"{flight} - {origin}-{destination}",
        }

    match = HOTEL_RE.match(cleaned)
    if match:
        city = match.group(1)
        return {
            **base,
            "activity_type": "hotel",
            "activity_code": "HOTEL",
            "hotel_city": city,
            "normalized_label": f"Hotel ({city})",
        }

    match = SBY_RE.match(cleaned)
    if match:
        code = f"SBY{match.group(1)}"
        return {
            **base,
            "activity_type": "standby",
            "activity_code": code,
            "normalized_label": code,
        }

    match = RSV_RE.match(cleaned)
    if match:
        code = f"RSV{match.group(1)}"
        return {
            **base,
            "activity_type": "reserve",
            "activity_code": code,
            "normalized_label": code,
        }

    if cleaned.upper() == "REST":
        return {
            **base,
            "activity_type": "rest",
            "activity_code": "REST",
            "normalized_label": "REST",
        }

    if cleaned.upper() == "F":
        return {
            **base,
            "activity_type": "day_off",
            "activity_code": "F",
            "normalized_label": "F",
        }

    return {
        **base,
        "activity_type": "other",
        "activity_code": "OTHER",
        "normalized_label": cleaned or "Unknown",
    }
