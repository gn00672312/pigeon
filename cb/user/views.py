# -*- coding: utf-8 -*-
from django.db import IntegrityError
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.views.decorators.cache import never_cache
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth import views as auth_views


from module import log
from .decorators import login_require
from .usecases import login as _login, logout as _logout, \
    verify_user, show_user, edit_user

import json

User = get_user_model()


class LoginView(auth_views.LoginView):
    @method_decorator(sensitive_post_parameters())
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        if request.is_ajax():
            context = {"code": None, "message": None}
            try:
                res = json.loads(request.body)
                username = res.get('username', None)
                password = res.get('password', None)

                user = _login(request, username, password)
                if user is not None:
                    context.update(
                        {"code": 200, "message": "OK", "username": user.username}
                    )
                else:
                    context.update({"code": 401, "message": "Unauthorized"})

            except:
                log.exception()
                context.update({"code": 500, "message": 'Internal Server Error'})

            return JsonResponse(context)
        else:
            return super().dispatch(request, *args, **kwargs)

@never_cache
def verify(request):
    context = {"code": None, "message": None}
    try:
        if verify_user(request.user):

            context.update({
                "code": 200, "message": "OK", "username": request.user.username,
                "is_super": request.user.is_superuser
            })
            # todo: permission check

        else:
            context.update({"code": 401, "message": "Unauthorized"})
    except:
        log.exception()
        context.update({"code": 500, "message": 'Internal Server Error'})

    return JsonResponse(context)


class LogoutView(auth_views.LogoutView):
    def get(self, request, *args, **kwargs):
        _logout(request)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            context = {"code": None, "message": None}
            try:
                _logout(request)
                context = {"code": 200, "message": "OK"}
            except:
                log.exception()
                context.update({"code": 500, "message": 'Internal Server Error'})
            return JsonResponse(context)
        else:
            return super().post(request, *args, **kwargs)

    def get_next_page(self):
        if self.request.is_ajax():
            return None
        else:
            return super().get_next_page()

@login_require
@never_cache
def profile(request):
    """
    show user profile by user pk.
    """
    context = {"code": None, "message": None, "result": None}
    pk = request.user.pk

    try:
        user = show_user(pk)
        if user is not None:
            context.update({"code": 200, "message": "OK",
                            "result": user})
        else:
            context.update({'code': 400, 'message': 'Bad Request',
                            'error': _("You didn't choose an user to show!")})

    except User.DoesNotExist:
        context.update({'code': 400, 'message': 'Bad Request',
                        'error': _('User does not exist in database!')})
    except Exception:
        log.exception()
        context.update({'code': 500, 'message': 'Server internal error'})

    return JsonResponse(context)


@login_require
@never_cache
def modify(request):
    """
    edit user by user pk.
    "username" is require in post data
    "first_name", "last_name"... are optional
    """
    context = {"code": None, "message": None, "result": None}

    # request.POST is an immutable instance.
    data = request.POST.copy()
    data.update({"pk": request.user.pk})
    try:
        is_valid, result = edit_user(data)

        if is_valid:
            context.update({"code": 200, "message": 'OK', "result": result})
            log.event('modifier: ', request.user.username, '.')

        else:
            context.update({"code": 400, "message": 'Bad Request',
                            "error": result})

    except User.DoesNotExist:
        context.update({"code": 400, "message": 'Bad Request',
                        "error": _('User does not exist in database!')})

    except IntegrityError:
        context.update({"code": 400, "message": 'Bad Request',
                        "error": _('An account with that username already exists.')})

    except Exception:
        log.exception('Edit user error.')
        context.update({"code": 500, "message": 'Server internal error'})

    return JsonResponse(context)
