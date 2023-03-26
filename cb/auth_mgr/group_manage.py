# -*- coding: utf-8 -*-
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import (
    get_user_model
)

from module import log
from . import permission_manage

User = get_user_model()

def as_dict(group):
    return {
        'id': group.id,
        'name': group.name,
        'permissions': [p.id for p in group.permissions.all()] if group and group.id is not None else [],
        'users': [user.id for user in group.user_set.all()] if group and group.id is not None else []
    }


def create(data):
    error_messages = {}
    group_name = data.get('name', None)

    if group_name == '':
        error_messages.update({
            'group_missing': 'The group name was missing.',
        })
    else:
        group = Group.objects.create(name=group_name)
        required_user = []
        for user in User.objects.all():
            user_status = data.get('user_id-%d' % user.id, None)
            if user_status:
                required_user.append(user)

        required_perms = []
        for permission in permission_manage.get_all():
            perm_status = data.get('permission_id-%d' % permission.id, None)
            if perm_status:
                required_perms.append(permission)

        if required_perms:
            group.permissions.set(required_perms)
        if required_user:
            group.user_set.set(required_user)

        group.save()
        log.event('A new group has been created. ID: ', group.id, '.')

        return group, None

    return group_name, error_messages


def modify(data):
    error_messages = {}
    group_id = data.get('group_id', None)
    group_name = data.get('name', None)

    member = []
    for user in User.objects.order_by("username").all():
        member_status = data.get('user_id-%d' % user.id, None)
        if member_status:
            member.append(user)

    required_perms = []
    for permission in permission_manage.get_all():
        perm_status = data.get('permission_id-%d' % permission.id, None)
        if perm_status:
            required_perms.append(permission)

    if group_id is None:
        error_messages.update({
            'group_missing': 'The group was missing.',
        })
    else:
        group = Group.objects.get(id=group_id)
        if group_name:
            group.name = group_name

        if member:
            group.user_set.set(member)

        if required_perms:
            group.permissions.set(required_perms)

        group.save()
        log.event('The group has been updated. ID: ', group.id, '.')

        return group, None

    return group_id, error_messages


def delete(data):
    error_messages = {}

    group_id = data.get('group_id', '')
    try:
        group = Group.objects.get(id=group_id)
        group.delete()
        return group, None

    except Group.DoesNotExist:
        error_messages.update({
            'group_missing': 'Group does not exist!'
        })

    return group_id, error_messages
