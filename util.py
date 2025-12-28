def minutes_to_hhmm(minutes: int) -> str:
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"


def iso_to_hhmm(iso_ts: str) -> str:
    return iso_ts[11:16]
