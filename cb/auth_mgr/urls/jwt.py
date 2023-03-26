from django.urls import path

from ..views.jwt import (
    obtain_jwt,
    refresh_jwt,
    verify_jwt,
)

urlpatterns = [
    path('jwt/obtain_token/', obtain_jwt, name='obtain_jwt'),
    path('jwt/refresh_token/', refresh_jwt, name='refresh_jwt'),
    path('jwt/verify_token/', verify_jwt, name='verify_jwt'),
]
