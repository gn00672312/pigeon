import unicodedata
from django.contrib.auth import (
    get_user_model
)
from django.contrib.auth.models import Group, Permission
from django.db import IntegrityError

from module import log

from . import permission_manage


User = get_user_model()


def as_dict(user):
    return {
        'id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'is_active': user.is_active,
        'is_superuser': user.is_superuser,
        'is_staff': user.is_staff,
        'groups': [g.id for g in user.groups.all()] if user and user.id is not None else [],
        'permissions': [p.id for p in user.user_permissions.all()] if user and user.id is not None else []
    }


def clean_username(username):
    return unicodedata.normalize('NFKC', username.strip())


def clean_password(password1, password2):
    if password1 != password2:
        return False, {
            'password_mismatch': 'The two password fields didn’t match.',
        }
    if not password1:
        """
        miss password 不算 error
        以 modify user 來說, miss password 表示不修改 password
        """
        return True, {
            'password_missing': 'The password was missing.',
        }
    return True, {}


def create(data):
    error_messages = {}

    username = data.get('username', None)
    password1 = data.get('password1', None)
    password2 = data.get('password2', None)
    email = data.get('email', '')
    first_name = data.get('first_name', '')
    last_name = data.get('last_name', '')
    is_superuser = data.get('is_superuser', False)
    if isinstance(is_superuser, str):
        is_superuser = True
    is_staff = data.get('is_staff', False)
    if isinstance(is_staff, str):
        is_staff = True
    is_active = data.get('is_active', False)
    if isinstance(is_active, str):
        is_active = True

    required_groups = []
    for group in Group.objects.all():
        gp_status = data.get('group_id-%d' % group.id, None)
        if gp_status:
            required_groups.append(group)

    required_perms = []
    for permission in permission_manage.get_all():
        perm_status = data.get('permission_id-%d' % permission.id, None)
        if perm_status:
            required_perms.append(permission)

    if not username:
        error_messages.update({
            'username_missing': 'The username was missing.',
        })

    _rs, _err = clean_password(password1, password2)
    if _err:
        error_messages.update(_err)

    user = User(
        username=clean_username(username),
        email=email,
        first_name=first_name,
        last_name=last_name,
        is_superuser=is_superuser,
        is_staff=is_staff,
        is_active=is_active
    )

    if error_messages:
        return user, error_messages

    try:
        user.set_password(password1)
        user.save()
        user.groups.set(required_groups)
        user.user_permissions.set(required_perms)

        return user, None

    except IntegrityError:
        log.exception('user_confilct')
        return user, {
            'user_confilct': 'An account with that username already exists.',
        }


def modify(data):
    error_messages = {}

    user_id = data.get('user_id', None)
    username = data.get('username', None)
    password1 = data.get('password1', None)
    password2 = data.get('password2', None)
    email = data.get('email', None)
    first_name = data.get('first_name', None)
    last_name = data.get('last_name', None)
    is_superuser = data.get('is_superuser', False)
    if isinstance(is_superuser, str):
        is_superuser = True
    is_staff = data.get('is_staff', False)
    if isinstance(is_staff, str):
        is_staff = True
    is_active = data.get('is_active', False)
    if isinstance(is_active, str):
        is_active = True

    required_groups = []
    for group in Group.objects.all():
        gp_status = data.get('group_id-%d' % group.id, None)
        if gp_status:
            required_groups.append(group)

    required_perms = []
    for permission in permission_manage.get_all():
        perm_status = data.get('permission_id-%d' % permission.id, None)
        if perm_status:
            required_perms.append(permission)

    try:
        user_id = int(user_id)
    except:
        error_messages.update({
            'user_missing': 'The user was missing.',
        })

    if not username:
        error_messages.update({
            'username_missing': 'The username was missing.',
        })

    _rs, _err = clean_password(password1, password2)
    if not _rs:
        error_messages.update(_err)

    user = User.objects.filter(id=user_id).first()
    if user is None:
        error_messages.update({
            'user_not_found': 'No such user.',
        })

    if error_messages:
        return user, error_messages

    try:
        user.username = clean_username(username)
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        if password1:
            user.set_password(password1)
        else:
            """keep orig password"""
        if is_superuser is not None:
            user.is_superuser = is_superuser
        if is_staff is not None:
            user.is_staff = is_staff
        if is_active is not None:
            user.is_active = is_active

        user.save()
        user.groups.set(required_groups)
        user.user_permissions.set(required_perms)

        return user, None

    except IntegrityError:
        log.exception('user_confilct')
        return user, {
            'user_confilct': 'An account with that username already exists.',
        }


def delete(data):
    error_messages = {}

    user_id = data.get('user_id', '')
    try:
        user = User.objects.get(id=user_id)

        # todo: remove user group, 也許 django 會自動刪掉, 要試試

        user.delete()
        return user, None

    except User.DoesNotExist:
        error_messages.update({
            'user_missing': 'User does not exist!'
        })

    return user_id, error_messages