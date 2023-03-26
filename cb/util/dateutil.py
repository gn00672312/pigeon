
from datetime import datetime
from dateutil import parser
from dateutil.tz import tzoffset


def parse_dtime(dtime):
    if "-" in dtime:
        try:
            dtime = parser.isoparse(dtime)
            tzinfo = dtime.tzinfo
            if tzinfo:
                dtime = dtime.astimezone(tzoffset(None, 0)).replace(tzinfo=None)
            return dtime, tzinfo
        except:
            pass

    else:
        try:
            if len(dtime) == 12:
                dtime = datetime.strptime(dtime, "%Y%m%d%H%M")
                return dtime, None
            if len(dtime) == 10:
                dtime = datetime.strptime(dtime, "%Y%m%d%H")
                return dtime, None
            if len(dtime) == 8:
                dtime = datetime.strptime(dtime, "%Y%m%d")
                return dtime, None
        except:
            pass

    dtime = parser.parse(dtime)
    tzinfo = dtime.tzinfo
    if tzinfo:
        dtime = dtime.astimezone(tzoffset(None, 0)).replace(tzinfo=None)
    return dtime, tzinfo


def format_dtime(dtime, tz=None):
    dtime = dtime.replace(second=0, microsecond=0)
    if tz:
        dtime = dtime.astimezone(tz)
    dt_str = dtime.strftime("%Y-%m-%dT%H:%M%z")
    if len(dt_str) >= 21:
        return dt_str[:19] + ":" + dt_str[19:21]
    else:
        return dt_str + "+00:00"


def parse_tzoffset(tz):
    """
    tz should be like +08:00 or -16:30
    秒以下放棄...
    """
    tz_offset_secs = 0
    negative = False
    if tz[0] == "+":
        tz = tz[1:]
    elif tz[0] == "-":
        tz = tz[1:]
        negative = True
    try:
        if len(tz) == 4:
            tz = [tz[:2], tz[2:]]
        else:
            tz = tz.split(":")
        tz_offset_secs = int(tz[0]) * 60 * 60
        if len(tz) > 1:
            tz_offset_secs += int(tz[1]) * 60
    except:
        return None

    if negative:
        tz_offset_secs *= -1

    return tzoffset(None, tz_offset_secs)
