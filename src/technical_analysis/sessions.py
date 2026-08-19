"""Session detection utilities

Return the current trading session given a timezone-aware timestamp.
"""
from typing import Dict, Any, Tuple
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo


def _parse_time(s: str) -> time:
    # expects 'HH:MM' format
    h, m = s.split(':')
    return time(int(h), int(m))


def get_session(timestamp: datetime, config: Dict[str, Any]) -> Dict[str, Any]:
    """Determine session for the given aware timestamp. Config contains session hours and timezone.

    Returns dict: session, session_start (iso), session_end (iso), overlap (bool), active (bool)
    """
    tz_name = config.get('session', {}).get('timezone', 'UTC')
    tz = ZoneInfo(tz_name)
    if timestamp.tzinfo is None:
        ts = timestamp.replace(tzinfo=tz)
    else:
        ts = timestamp.astimezone(tz)

    sessions_cfg = config.get('session', {})
    # each session defined as {'start': 'HH:MM', 'end': 'HH:MM'} in config
    def in_session(now: datetime, start_s: str, end_s: str) -> Tuple[datetime, datetime, bool]:
        start_t = _parse_time(start_s)
        end_t = _parse_time(end_s)
        today = now.date()
        start_dt = datetime.combine(today, start_t, tzinfo=tz)
        end_dt = datetime.combine(today, end_t, tzinfo=tz)
        if end_dt <= start_dt:
            # crosses midnight
            end_dt = end_dt + timedelta(days=1)
        return start_dt, end_dt, start_dt <= now < end_dt

    asian = sessions_cfg.get('asian', {'start': '00:00', 'end': '08:00'})
    london = sessions_cfg.get('london', {'start': '07:00', 'end': '15:00'})
    newy = sessions_cfg.get('newyork', {'start': '12:00', 'end': '20:00'})

    a_s, a_e, a_in = in_session(ts, asian['start'], asian['end'])
    l_s, l_e, l_in = in_session(ts, london['start'], london['end'])
    n_s, n_e, n_in = in_session(ts, newy['start'], newy['end'])

    overlap = False
    session = 'OUTSIDE_MAJOR_SESSION'
    session_start = None
    session_end = None
    if l_in and n_in:
        session = 'LONDON_NEW_YORK_OVERLAP'
        overlap = True
        session_start = max(l_s, n_s).isoformat()
        session_end = min(l_e, n_e).isoformat()
    elif l_in:
        session = 'LONDON'
        session_start = l_s.isoformat()
        session_end = l_e.isoformat()
    elif n_in:
        session = 'NEW_YORK'
        session_start = n_s.isoformat()
        session_end = n_e.isoformat()
    elif a_in:
        session = 'ASIAN'
        session_start = a_s.isoformat()
        session_end = a_e.isoformat()
    else:
        session = 'OUTSIDE_MAJOR_SESSION'
        # determine next session start/end for info
        session_start = None
        session_end = None

    # session quality mapping
    quality_map = sessions_cfg.get('quality', {'LONDON':'HIGH','NEW_YORK':'HIGH','LONDON_NEW_YORK_OVERLAP':'HIGH','ASIAN':'MEDIUM','OUTSIDE_MAJOR_SESSION':'LOW'})
    session_quality = quality_map.get(session, 'LOW')

    return {
        'session': session,
        'session_start': session_start,
        'session_end': session_end,
        'overlap': overlap,
        'active': True if session != 'OUTSIDE_MAJOR_SESSION' else False,
        'quality': session_quality,
        'checked_at': datetime.utcnow().replace(tzinfo=ZoneInfo('UTC')).isoformat()
    }
