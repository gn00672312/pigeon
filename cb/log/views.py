import os
import glob
from datetime import datetime
from django.conf import settings
from django.shortcuts import (
    render
)
from cb.auth_mgr.decorators import staff_required


TOP = 80


class Message(object):
    def __init__(self, keywords=None):
        self.keywords = keywords
        self.lines = []
        self.prefix = ""

    def parse(self, line):
        msg = []
        if len(line) > 0 and line[0] == "[":
            msg = self.pack()
            line = self.parse_prefix(line)
        self.lines.append(line)
        return msg

    def end(self):
        msg = self.pack()
        return msg

    def parse_prefix(self, line):
        self.prefix = ""
        idx = line.find("]")
        if idx > 1:
            self.prefix = line[1:idx]
            if len(line) > (idx+1):
                line = line[idx+1:]
            else:
                line = ""
        return line

    def pack(self):
        msg = []
        if self.prefix and self.lines:
            msg = [
                self.prefix,
                "<br/>".join(self.lines)
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


@staff_required
def index(request):
    template = 'log/index.html'

    context = {
        "collects": [],
        "collect": "",
        "messages": [],
        "query_path": ""
    }

    if hasattr(settings, "LOG_VIEWER_COLLECT"):
        collects = settings.LOG_VIEWER_COLLECT
        context["collects"] = collects
        if len(collects) > 0:
            log_dir = os.environ.get('LOG_DIR', None)
            if log_dir:

                selected_collect = request.GET.get("collect", None)
                if not selected_collect:
                    selected_collect = collects[0]
                context["collect"] = selected_collect

                context["query_path"] = "?"
                dt = request.GET.get("dt")
                if not dt:
                    dt = datetime.utcnow().strftime("%Y-%m-%d")
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
                            msg = message.parse(line)
                            if msg:
                                contexts.append(msg)
                    msg = message.end()
                    if msg:
                        contexts.append(msg)
                    return contexts

                pathname = os.path.join(log_dir, selected_collect+"."+dt+".log")
                if os.path.exists(pathname):
                    context["messages"].extend(_parse_log(pathname))
                else:
                    pathname = os.path.join(log_dir, selected_collect+".log")
                    if os.path.exists(pathname):
                        context["messages"].extend(_parse_log(pathname))

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

    return render(request, template, context)
