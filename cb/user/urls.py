# -*- coding: utf-8 -*-
from django.conf.urls import url

from .views import verify, profile, modify


urlpatterns = [
    url(r'^verify/?$', verify, name="user-verify"),
    url(r'^profile/?$', profile, name="user-profile"),
    url(r'^modify/?$', modify, name="user-modify"),
]
