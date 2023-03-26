# -*- coding: utf-8 -*-
from django.contrib.auth import authenticate, login as _login,\
                                logout as _logout
from django.contrib.auth import get_user_model

from module import log
from cb.user.forms import EditUserForm

User = get_user_model()


def login(request, username, password):
    user = authenticate(request,
                        username=username,
                        password=password)

    if user is not None:
        _login(request, user)
        log.event('User logged in: ', user)

    return user


def logout(request):
    user = request.user

    if user is not None:
        _logout(request)
        log.event('User logged out: ', user)

    return user


def verify_user(user):
    return user.is_authenticated


def show_user(pk, to_dict=True):
    if pk is None:
        log.problem("You didn't choose an user to show!")
        return None
    else:
        u = User.objects.get(pk=pk)
        return user_as_dict(u) if to_dict else u


def edit_user(data, to_dict=True):
    form = EditUserForm(data=data)
    if form.is_valid():
        user = form.save()
        result = user_as_dict(user) if to_dict else user

        log.event('User information has been modified. ID: ', user.username, '.')
    else:
        result = [e.as_text() for e in form._errors.values()]

    return form.is_valid(), result


def user_as_dict(user):
    return {'pk': user.id,
            'username': user.username,
            'first-name': user.first_name,
            'last-name': user.last_name,
            'email': user.email,
            'active': user.is_active}
