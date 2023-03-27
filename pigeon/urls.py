""" URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  path('blog/', include(blog_urls))
"""
from django.urls import path, re_path
from django.conf import settings
from django.views.static import serve
from django.conf.urls import include
from django.contrib import admin

from pigeon.home import urls as home

from cb.user.views import LoginView
from cb.user.views import LogoutView

from cb.user import urls as user

urlpatterns = [
    path('', include(home)),
    path('admin/', admin.site.urls),

    path('user/login/', LoginView.as_view(template_name='registration/login.html'), name='user_login'),
    path('user/logout/', LogoutView.as_view(), name='user_logout'),
    path('user/', include(user)),
    path("accounts/", include("django.contrib.auth.urls")),

    re_path(r'^static/(?P<path>.*)$', serve, kwargs={'document_root': settings.STATIC_ROOT}),
    re_path(r'^media/(?P<path>.*)$', serve, kwargs={'document_root': settings.MEDIA_ROOT}),
]
