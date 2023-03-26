from django.urls import path
from .views import index


app_name = "module_log"
urlpatterns = [
    path('', index, name='index'),
]
