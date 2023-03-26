# -*- coding: utf-8 -*-
import os

from django.contrib.auth.models import Permission
from django.conf import settings

from module import log
from cb.util import config
from .models import PermissionRepository


def get_all():
    """
    2019-08-21@lwsu
      try to load function permission config
    """
    if hasattr(settings, "FUNC_PERMISSION_CONFIG"):
        try:
            func_perm_conf = config.load(settings.FUNC_PERMISSION_CONFIG).get(
                "FUNC_PERMISSION", None)
        except :
            log.exception()
            return []

        if func_perm_conf:
            def _func_exists(codename):
                for key, value in func_perm_conf:
                    if key == codename:
                        return True
                return False

            # set 1: check removed
            for pr in PermissionRepository.objects.all():
                if not _func_exists(pr.permission.codename):
                    pr.delete()
                    # 相關 user permossion and group permission 會自動被刪掉
                    pr.permission.delete()

            # set 2: check added
            for p_code, p_name in func_perm_conf:
                permission = PermissionRepository.find_permission(codename=p_code)
                if permission:
                    if not permission.name == p_name:
                        # update permission.name
                        permission.name = p_name
                        permission.save()
                else:
                    PermissionRepository.create_permission(codename=p_code, name=p_name)

    return [pr.permission for pr in PermissionRepository.objects.all()]
