# -*- coding: utf-8 -*-
from rest_framework import permissions


class APIPermissions(permissions.BasePermission):
    perms = []

    def has_permission(self, request, view):
        user = request.user
        if hasattr(user, 'is_superuser') and user.is_superuser:
            return True

        for perm in user.user_permissions.all():
            if perm.codename in self.perms:
                return True

        for group in user.groups.all():
            for perm in group.permissions.all():
                if perm.codename in self.perms:
                    return True

        return False
