from django.shortcuts import render

from cb.auth_mgr.decorators import staff_required


@staff_required
def index(request):

    context = {}
    return render(request, 'console/index.html', context)
