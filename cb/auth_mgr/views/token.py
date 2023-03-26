from django.contrib.auth import login, logout, user_logged_in, user_logged_out
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from ..serializers.token import TokenCreateSerializer, TokenSerializer


User = get_user_model()


def login_user(request, user):
    token, _ = Token.objects.get_or_create(user=user)
    # if settings.CREATE_SESSION_ON_LOGIN:
    #     login(request, user)
    # user_logged_in.send(sender=user.__class__, request=request, user=user)
    return token


class TokenCreateView(generics.GenericAPIView):
    """
    Use this endpoint to obtain user authentication token.
    """
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = "auth_mgr/token.html"
    serializer_class = TokenCreateSerializer
    permission_classes = [AllowAny]

    def get(self, request, **kwargs):
        if request.user.is_authenticated:
            token, _ = Token.objects.get_or_create(user=request.user)
            return self._action(token)
        else:
            import django
            from django.conf import settings
            django.setup()

            if getattr(settings, "LOGIN_URL_NAME", None):
                return redirect(reverse(settings.LOGIN_URL_NAME))
            else:
                return Response(
                    data={},
                    status=status.HTTP_200_OK
                )

    def post(self, request, **kwargs):
        if request.data.get("form_action") == "logout":
            logout(request)
            return Response(
                data={},
                status=status.HTTP_200_OK
            )

        if request.user.is_authenticated:
            user = request.user
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.user
        if request.data.get("regen", None):
            Token.objects.filter(user=request.user).delete()
        token, _ = Token.objects.get_or_create(user=user)

        # keep user in request
        login(request, user)
        return self._action(token)

    def _action(self, token):
        return Response(
            data=TokenSerializer(token).data,
            status=status.HTTP_200_OK
        )


# obtain_token = token_views.ObtainAuthToken.as_view()

obtain_token = TokenCreateView.as_view()
