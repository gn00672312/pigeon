# -*- coding: utf-8 -*-
from django.urls import re_path


from .views import (
    user_management,
    create_user, modify_user, delete_user,
)

app_name = 'pigeon_auth_mgr'
urlpatterns = [
    re_path(r'^$', user_management, name="user_management"),

    re_path(r'^user/create/$', create_user, name="create_user"),
    re_path(r'^user/modify/(?P<user_id>\d+)/$', modify_user, name="modify_user"),
    re_path(r'^user/delete/$', delete_user, name="delete_user"),
]
