
from django.shortcuts import render

from cb.auth_mgr.decorators import func_required


def index(request):
    context = {}

    html = 'home/index.html'
    return render(request, html, context)


@func_required('func_score_quanmin')
def score_quanmin(request):
    name = '全民海翔聯合會'
    context = {"name": name}

    html = 'home/score.html'
    return render(request, html, context)


@func_required('func_score_3678')
def score_3678(request):
    name = '3678聯合會'
    context = {"name": name}

    html = 'home/score.html'
    return render(request, html, context)
