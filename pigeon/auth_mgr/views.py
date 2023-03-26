from django.shortcuts import (render, redirect)
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.utils.translation import ugettext as _

from django.contrib.auth.models import Group

from cb.auth_mgr import (
    permission_manage,
    user_manage)

from module import log

User = get_user_model()


@csrf_protect
@never_cache
def user_management(request, template_name="auth_mgr/user_management.html"):
    return render(request, template_name, {
        'users': User.objects.order_by("username").all()
    })


@csrf_protect
@never_cache
def create_user(request, template_name="auth_mgr/edit_user.html"):
    """
    create user.
    The "username" is require in post data,
    "groups" and "permissions" is optional.
    Using "account" instead of "user,
    because "user" is defined in request.
    """
    if request.method == "GET":
        return_to = request.META.get('HTTP_REFERER', '')
        return render(request, template_name, {
            'groups': Group.objects.all(),
            'permissions': permission_manage.get_all(),
            'return_to': return_to
        })

    else:
        data = request.POST.copy()
        return_to = data.get('return_to', '')
        context = {'return_to': return_to}
        try:
            user, error = user_manage.create(data)
            if not error:
                log.event('editor: ', request.user.username, '.')
                if return_to:
                    return redirect(return_to)
                context.update({"code": 200})
            else:
                context.update({
                    "code": 400, "message": error,
                })
            context.update({
                "account": user_manage.as_dict(user),
                "groups": Group.objects.all(),
                "permissions": permission_manage.get_all()
            })
        except Exception:
            log.exception('Create new user error.')
            context.update({"code": 500, "message": 'Server internal error'})

        return render(request, template_name, context)


@csrf_protect
@never_cache
def modify_user(request, user_id, template_name="auth_mgr/edit_user.html"):
    """
    modify user.
    The "user_id" is require in post data,
    "groups" and "permissions" is optional
    Using "account" instead of "user,
    because "user" is defined in request.
    """
    if request.method == "GET":
        return_to = request.META.get('HTTP_REFERER', '')
        context = {'return_to': return_to}
        try:
            user = User.objects.get(id=user_id)
            context.update({
                'account': user_manage.as_dict(user),
                'groups': Group.objects.all(),
                'permissions': permission_manage.get_all(),
            })
        except User.DoesNotExist:
            context.update({"error": _('User does not exist!')})
        return render(request, template_name, context)
    else:
        data = request.POST.copy()
        return_to = data.get('return_to', '')
        context = {'return_to': return_to}
        try:
            user, error = user_manage.modify(data)
            if not error:
                log.event('editor: ', request.user.username, '.')
                if return_to:
                    return redirect(return_to)
                context.update({"code": 200})
            else:
                context.update({"code": 400, "message": error})
            context.update({
                "account": user_manage.as_dict(user),
                'groups': Group.objects.all(),
                'permissions': permission_manage.get_all(),
            })
        except Exception:
            log.exception('Modify user error.')
            context.update({"code": 500, "error": 'Server internal error'})

        return render(request, template_name, context)


@csrf_protect
@never_cache
def delete_user(request, template_name="auth_mgr/edit_user.html"):
    """
    delete group by group id.
    "group_id" is require in post data
    """
    if request.method == "GET":
        return render(request, template_name, {})
    else:
        data = request.POST.copy()
        return_to = data.get('return_to', '')
        context = {'return_to': return_to}
        try:
            user_id, error = user_manage.delete(data)
            if not error:
                log.event('editor: ', request.user.username, '.')
                if return_to:
                    return redirect(return_to)
                context.update({"code": 200})
            else:
                context.update({"code": 400, "message": error})

        except Exception:
            log.exception('Deleted group error.')
            context.update({'code': 500, 'error': 'Server internal error'})

        return render(request, template_name, context)
