from django.urls import path
from cb.log.views import index


urlpatterns = [
    path('', index, name='index'),
]
