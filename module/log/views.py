import os
import glob
import pytz
from datetime import datetime
import time
from django.conf import settings
from django.shortcuts import (
    render
)
from module import log

TOP = 120
LOG_TZ = os.getenv('LOG_TZ')

import re

LOG_TIME_RE = re.compile(r'.*(?P<logtime>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\,\d{3}.*')


def _parse_log_time(line):
    mo = LOG_TIME_RE.match(line)
    if mo:
        return datetime.strptime(mo.groupdict()['logtime'],
                                 '%Y-%m-%d %H:%M:%S')
    return None


def _requiretime_gt_logtime(requiretime, logtime):
    if (requiretime.tm_hour * 60 + requiretime.tm_min) > (logtime.hour * 60 + logtime.minute):
        return True
    return False


def _requiretime_lt_logtime(requiretime, logtime):
    if (requiretime.tm_hour * 60 + requiretime.tm_min) < (logtime.hour * 60 + logtime.minute):
        return True
    return False


class Message(object):
    def __init__(self, keywords=None):
        self.keywords = keywords
        self.lines = []
        self.prefix = ""
        self.logtimg = None

    def parse(self, line):
        msg = []
        self.logtimg = None
        if len(line) > 0 and line[0] == "[":
            msg = self.pack()
            line = self.parse_prefix(line)
        self.lines.append(line)
        return msg, self.logtimg

    def end(self):
        msg = self.pack()
        return msg, self.logtimg

    def parse_prefix(self, line):
        self.prefix = ""
        idx = line.find("]")
        if idx > 1:
            self.prefix = line[1:idx]
            self.logtimg = _parse_log_time(self.prefix)
            if len(line) > (idx + 1):
                line = line[idx + 1:]
            else:
                line = ""
        return line

    def pack(self):
        msg = []
        if self.prefix and self.lines:
            msg = [
                self.prefix,
                "<br/>".join(self.lines) + "<br/>"
            ]
            if self.keywords:
                for kw in self.keywords:
                    if len(kw) > 1:
                        if kw[0] == "!":
                            kw = kw[1:]
                            if kw in msg[0] or kw in msg[1]:
                                msg = []
                                break
                        else:
                            if kw not in msg[0] and kw not in msg[1]:
                                msg = []
                                break
        self.lines = []
        return msg


def key_of_collect(collect):
    if collect:
        if isinstance(collect, (tuple, list)):
            return collect[0]
        return collect
    return None


def pair_of_collect(collect):
    if isinstance(collect, (tuple, list)):
        return collect
    return (collect, collect)


def index(request, template_name='log/index.html'):
    """
    把 default page 分出來
    這裏自己寫權限控管, 不用 module.auth_mgr 的
    這樣 module 比較獨立
    """
    return log_index(request, template_name)
    # user = request.user
    # if user and user.is_authenticated:
    #     if user.is_superuser or user.is_staff:
    #         return log_index(request, template_name)
    # from django.contrib.auth.views import redirect_to_login
    # from django.shortcuts import resolve_url
    # return redirect_to_login(
    #     request.build_absolute_uri(), resolve_url(settings.LOGIN_URL))


def log_index(request, template_name):
    """
    把顯示頁分出來
    這樣方便系統擴充
    """
    context = {
        "collects": [],
        "collect": "",
        "messages": [],
        "query_path": ""
    }

    if hasattr(settings, "LOG_VIEWER_COLLECT"):
        collects = settings.LOG_VIEWER_COLLECT
        context["collects"] = [pair_of_collect(collect) for collect in collects]
        if len(collects) > 0:
            log_dir = os.environ.get('LOG_DIR', None)
            if log_dir:

                selected_collect_key = request.GET.get("selected_collect", None)
                for collect in collects:
                    if selected_collect_key == key_of_collect(collect):
                        context["selected_collect"] = selected_collect_key
                        break
                else:
                    selected_collect_key = key_of_collect(collects[0])
                    context["selected_collect"] = selected_collect_key

                context["query_path"] = "?"
                dt = request.GET.get("dt")
                if dt:
                    try:
                        dt = datetime.strptime(dt, "%Y-%m-%d")
                    except:
                        dt = None
                if not dt:
                    if LOG_TZ:
                        dt = datetime.utcnow().replace(tzinfo=pytz.UTC)
                        dt = dt.astimezone(pytz.timezone(LOG_TZ))
                    else:
                        dt = datetime.now()

                tfrom = tto = None
                time_range = request.GET.get("time_range")
                try:
                    if time_range and "-" in time_range:
                        tfrom, tto = time_range.split("-")
                    if tfrom:
                        tfrom = time.strptime(tfrom, "%H:%M")
                    if tto:
                        tto = time.strptime(tto, "%H:%M")
                except:
                    tfrom = tto = None

                context["time_range"] = ""
                if tfrom:
                    context["time_range"] = time.strftime("%H:%M", tfrom) + "-"
                if tto:
                    if not tfrom:
                        context["time_range"] = "-"
                    context["time_range"] = context["time_range"] + time.strftime("%H:%M", tto)

                dt = dt.strftime("%Y-%m-%d")
                context["dt"] = dt
                context["query_path"] += "dt=" + dt
                keywords = request.GET.get("q", "")
                if keywords:
                    context["q"] = keywords
                    context["query_path"] += "&q=" + keywords
                    keywords = keywords.split(" ")

                def _parse_log(pathname):
                    contexts = []
                    message = Message(keywords)
                    with open(pathname) as ff:
                        for line in ff:
                            msg, logtimg = message.parse(line)
                            if msg:
                                if tfrom and _requiretime_gt_logtime(tfrom, logtimg):
                                    continue
                                if tto and _requiretime_lt_logtime(tto, logtimg):
                                    continue
                                contexts.append(msg)
                    msg, logtimg = message.end()
                    while msg:
                        # this is the last message
                        if tfrom and _requiretime_gt_logtime(tfrom, logtimg):
                            break
                        if tto and _requiretime_lt_logtime(tto, logtimg):
                            break
                        contexts.append(msg)
                        break
                    return contexts

                pathname = os.path.join(log_dir, selected_collect_key + "." + dt + ".log")
                if os.path.exists(pathname):
                    context["messages"].extend(_parse_log(pathname))
                else:
                    pathname = os.path.join(log_dir, selected_collect_key + ".log")
                    if os.path.exists(pathname):
                        context["messages"].extend(_parse_log(pathname))

                # 反向排序
                context["messages"] = context["messages"][::-1]
                top = int(request.GET.get("top", TOP))
                context["top"] = top
                context["query_path"] += "&top=" + str(top)
                if top == 0:
                    pass
                else:
                    if top > len(context["messages"]):
                        top = len(context["messages"])
                    context["messages"] = context["messages"][0:top]

    return render(request, template_name, context)
