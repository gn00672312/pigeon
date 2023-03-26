from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dateutil import parser
from dateutil.tz import tzoffset
import calendar


class DateFactory(object):
    def __init__(self):
        self.t = self.now()

    @classmethod
    def now(cls):
        # 取得現在時間
        t = datetime.now()
        return t

    @classmethod
    def yesterday(cls):
        # 取得一天前的時間
        y = datetime.now() - timedelta(days=1)
        y = y.replace(hour=0, minute=0, second=0, microsecond=0)
        return y

    @classmethod
    def to_month_begin(cls, dt, is_date=False):
        dt = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return dt.date() if is_date else dt

    @classmethod
    def to_month_end(cls, dt, is_date=False):
        dt = dt.replace(day=1, hour=23, minute=59, second=59) + relativedelta(months=1) - timedelta(days=1)
        return dt.date() if is_date else dt

    @classmethod
    def month_range(cls, date):
        # 取得指定日期該月的第一天和最後一天
        ms = cls.to_month_begin(date)
        me = cls.to_month_end(ms)
        # 取得這個月的天數
        md = calendar.monthrange(date.year, date.month)[1]
        return ms, me, md

    def thismonth(self):
        return self.month_range(self.t)

    def lastmonth(self):
        return self.month_range(self.t - relativedelta(months=1))

    def nextmonth(self, day):
        day, _ = self.parse_dtime(day)
        # day = day.to_pydatetime()
        # 取得輸入日期的年和月
        y = day.year
        m = day.month
        # 取得這個月的天數
        ds = calendar.monthrange(y, m)[1]
        tnm = day + timedelta(days=ds)
        return tnm

    @classmethod
    def totoday(cls):
        # 取得一天前的時間
        y = datetime.now() - timedelta(days=1)
        y = y.date()
        # 取得本月到上一天為止的天數
        tot = y.day
        return tot

    @classmethod
    def trandate(cls, day):
        # 把字串datetime轉成datetime的形式
        ag, _ = cls.parse_dtime(day)
        return ag

    @classmethod
    def pd_to_py_date(cls, day):
        # 把pd datetime轉成datetime的形式
        ag = day.to_pydatetime()
        return ag

    @classmethod
    def pd_to_py_month_end(cls, day):
        day = day.to_pydatetime()
        # 取得輸入日期的年和月
        y = day.year
        m = day.month
        # 取得這個月的天數
        ds = calendar.monthrange(y, m)[1]
        tnm = day + timedelta(days=ds) - timedelta(seconds=1)
        return tnm

    @classmethod
    def parse_dtime(cls, dtime):
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

    @classmethod
    def format_dtime(cls, dtime, tz=None):
        """
        這個 function 主要是幫忙 format
        tz 參數的使用必須配合這個 dtime 是有 tzinfo property
        因為, 如果 dtime 沒有 tzinfo, 執行 astimezone 時會變成用系統的時區當 dtime 的時區
        (這裏的系統時區, 也無法確定的 os 的還是 django, 看從哪裏呼叫...)
        也就是說, 很有可能 astimezone 會得到非預期的結果...
        例如從資料庫取出的資料可能沒有 tzinfo, 但該資料其實是 LocalTime, 而我們系統又設定 UTC 時區
        所以, 如果要用 tz 參數, 使用者必須先行為 dtime 加上 tzinfo (如果原本沒有的話)
        否則會 raise Exception
        """
        dtime = dtime.replace(second=0, microsecond=0)
        if tz:
            if dtime.tzinfo is None:
                raise Exception("The property tzinfo of this datetime object is None")
            dtime = dtime.astimezone(tz)
        dt_str = dtime.strftime("%Y-%m-%dT%H:%M%z")
        if len(dt_str) >= 21:
            return dt_str[:19] + ":" + dt_str[19:21]
        else:
            return dt_str + "+00:00"

    @classmethod
    def parse_tzoffset(cls, tz):
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
