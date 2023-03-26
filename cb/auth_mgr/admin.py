# -*- coding: utf-8 -*-

from django.contrib import admin
from django.contrib.auth.models import (
    Permission, ContentType
)

admin.site.register(Permission)
admin.site.register(ContentType)
