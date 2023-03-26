from django.urls import path

from ..views.token import obtain_token

urlpatterns = [
    path("token/obtain_token/", obtain_token, name="obtain_api_token"),
    # path('obtain_token/', obtain_token, name='obtain_auth_token'),
]

# example
# curl -X POST -H 'Content-Type:application/json' --data '{"username":"$USER","password":"$PASS"}' "http://127.0.0.1:$PORT/api_auth/token/obtain_token/"
