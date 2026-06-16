import requests
from datetime import datetime, timedelta


def get_calendar_events(calendar_id, api_key):
    """
    Fetch upcoming events from a public Google Calendar.
    calendar_id: calendar ID (e.g. email@group.calendar.google.com)
    api_key: Google Cloud API key with Calendar API enabled
    """
    if not api_key:
        raise ValueError("Google API key required. Enable the Calendar API in Google Cloud Console.")

    now = datetime.utcnow().isoformat() + "Z"
    end = (datetime.utcnow() + timedelta(days=14)).isoformat() + "Z"

    url = "https://www.googleapis.com/calendar/v3/calendars/{}/events".format(
        requests.utils.quote(calendar_id, safe="")
    )
    params = {
        "timeMin": now,
        "timeMax": end,
        "maxResults": 20,
        "singleEvents": "true",
        "orderBy": "startTime",
        "key": api_key,
    }

    try:
        r = requests.get(url, params=params, timeout=15)
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Cannot reach Google APIs.")

    if not r.ok:
        body = r.json()
        msg = body.get("error", {}).get("message", r.text[:200])
        raise RuntimeError("Calendar API error: {}".format(msg))

    events = r.json().get("items", [])

    parsed = []
    for e in events:
        start = e.get("start", {})
        parsed.append({
            "title": e.get("summary", "Untitled"),
            "date": start.get("date") or start.get("dateTime", "")[:10],
            "type": _classify_event(e.get("summary", "")),
        })

    return {
        "upcoming_events": len(events),
        "events": parsed,
        "has_review_meeting": any("review" in e["title"].lower() for e in parsed),
        "has_deadline": any(e["type"] == "deadline" for e in parsed),
    }


def _classify_event(title):
    t = title.lower()
    if any(w in t for w in ["deadline", "due", "submit", "submission"]):
        return "deadline"
    if any(w in t for w in ["review", "check", "standup", "sync"]):
        return "review"
    return "meeting"
