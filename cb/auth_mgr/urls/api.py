from django.urls import path

from ..views.api import RemoteAuth


urlpatterns = [
    path('api/remote_auth/', RemoteAuth.as_view({'post': 'post'}), name='remote_auth_api')
]
