# -*- coding: utf-8 -*-
from django.conf.urls import url

from ..views.base import (
    user_management,
    group_management,
    create_user, modify_user, delete_user,
    create_group, modify_group, delete_group
)

app_name = 'cb_auth_mgr'
urlpatterns = [
    url(r'^$', user_management, name="user_management"),

    url(r'^user/create/$', create_user, name="create_user"),
    url(r'^user/modify/(?P<user_id>\d+)/$', modify_user, name="modify_user"),
    url(r'^user/delete/$', delete_user, name="delete_user"),

    url(r'^group/$', group_management, name="group_management"),
    url(r'^group/create/$', create_group, name="create_group"),
    url(r'^group/modify/(?P<group_id>\d+)/$', modify_group, name="modify_group"),
    url(r'^group/delete/$', delete_group, name="delete_group"),
]
