
from django.shortcuts import render


def index(request):
    context = {'logs': []}

    html = 'home/index.html'
    return render(request, html, context)
