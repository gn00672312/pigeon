from django.urls import path
from .views import index, score_quanmin, score_3678

app_name = 'home'
urlpatterns = [
    path('', index, name='home'),
    path('score/quanmin/', score_quanmin, name='score_quanmin'),
    path('score/3678/', score_3678, name='score_3678'),
]
