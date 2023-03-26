# -*- coding: utf-8 -*-
from django.urls import path

from pigeon.console.views import (
    index
)

app_name = 'console'

urlpatterns = [
    path('', index, name='console'),
]
