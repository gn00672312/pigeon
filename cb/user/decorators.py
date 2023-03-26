# -*- coding: utf-8 -*-
from django.http import JsonResponse


def login_require(view_func):
    def _login_require(request, *args, **kwargs):
        context = {"code": None, "message": None}

        if request.user.is_authenticated and request.user.is_active:
            return view_func(request, *args, **kwargs)

        else:
            context["code"] = 401
            context["message"] = 'Unauthorized'

        return JsonResponse(context)

    return _login_require
