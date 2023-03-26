# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import Permission, ContentType


class PermissionRepository(models.Model):
    permission = models.OneToOneField(Permission, on_delete=models.CASCADE,
                                      related_name='status')

    class Meta:
        default_permissions = ()
        db_table = 'cb_permission_repository'
        app_label = 'auth_mgr'
        # can set extra permission here, for example :
        # permissions = (
        #     ("can_query_question", "可以查問題"),
        #     ("can_do_vote", u"可以投票"),
        # )

    def __str__(self):
        return str(self.id) + '|' + str(self.permission)

    @classmethod
    def create_permission(cls, codename, name, content_type=None):
        if content_type is None:
            content_type = ContentType.objects.get_for_model(
                PermissionRepository)

        permission = Permission.objects.filter(
            codename=codename, content_type=content_type,
        ).first()
        if permission is None:
            permission, created = Permission.objects.get_or_create(
                codename=codename, name=name, content_type=content_type,
            )
        return cls.objects.get_or_create(permission=permission)

    @classmethod
    def modify_permission(cls, pk, codename, name):
        try:
            permission = Permission.objects.get(pk=pk)
        except Permission.DoesNotExist:
            raise
        else:
            permission.codename = codename
            permission.name = name
            permission.save()

        context = {}

        context.update({
            'pk': permission.id, 'name': permission.name,
            'codename': permission.codename,
            'error': ''
        })

        return permission, context

    @classmethod
    def find_permission(cls, pk=None, codename=None, content_type=None):
        if content_type is None:
            content_type = ContentType.objects.get_for_model(
                PermissionRepository)
        if pk is None and codename is None:
            raise Permission.DoesNotExist
        if pk:
            permission = Permission.objects.get(pk=pk)
        else:
            permission = Permission.objects.filter(
                codename=codename, content_type=content_type,
            ).first()
        return permission
