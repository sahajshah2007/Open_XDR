from datetime import datetime, timezone


def utc_timestamp(value=None):
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, (float, int)):
        parsed = datetime.fromtimestamp(value, timezone.utc)
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def tactic_name(value):
    return str(value).lower().replace(" ", "-").replace("_", "-") if value else None
