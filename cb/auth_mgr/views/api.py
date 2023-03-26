"""
2020-02-21@lwsu
  提供 3 個 API
  auth, get_user_profile, create_user
  這是給聯盟系統 backend 用的
  perms 直接使用 django permission 機制 (可直接使用 django admin 管理)
"""
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import GenericViewSet
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token

from django.contrib.auth import (
    authenticate, get_user_model
)
from cb.auth_mgr.api_permission import APIPermissions

from ..serializers.token import UserSerializer

User = get_user_model()


class UserAuth(APIView):
    perms = ["auth.user.change_user"]

    def get_view_description(self, html=False):
        # todo
        return ''

    def options(self, request, *args, **kwargs):
        # todo
        return Response({}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        context = {
            "message": ""
        }
        status_code = status.HTTP_200_OK

        username = request.data.get("username")
        password = request.data.get("password")
        if username is not None and password:
            user_cache = authenticate(request, username=username, password=password)
            if user_cache is None:
                status_code = status.HTTP_403_FORBIDDEN
                context["message"] = ""
            elif not user_cache.is_active:
                status_code = status.HTTP_403_FORBIDDEN
                context["message"] = ""

        return Response(context, status=status_code)


class UserCreate(APIView):
    perms = ["auth.user.add_user"]

    def get_view_description(self, html=False):
        # todo
        return ''

    def options(self, request, *args, **kwargs):
        # todo
        return Response({}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        context = {
            "message": ""
        }
        status_code = status.HTTP_201_CREATED

        username = request.data.get("username")
        password = request.data.get("password")
        try:
            user = User.objects.get(username=username)
            status_code = status.HTTP_409_CONFLICT
        except:
            user = User(username=username)
            user.save(commit=False)
            user.set_password(password)
            user.save()

        return Response(context, status=status_code)


class UserProfile(APIView):
    perms = ["auth.user.view_user"]

    def get_view_description(self, html=False):
        # todo
        return ''

    def options(self, request, *args, **kwargs):
        # todo
        return Response({}, status=status.HTTP_200_OK)

    def get(self, request, *args, **kwargs):
        context = {
            "message": "",
            "data": {}
        }
        status_code = status.HTTP_200_OK

        username = request.query_params.get("username")
        try:
            user = User.objects.get(username=username)
            context["data"]["first_name"] = user.first_name
            context["data"]["last_name"] = user.last_name
            context["data"]["email"] = user.email
        except:
            status_code = status.HTTP_404_NOT_FOUND

        return Response(context, status=status_code)


class RemoteAuth(GenericViewSet):
    serializer_class = UserSerializer
    authentication_classes = []
    permission_classes = [AllowAny]

    def get_object(self, token):
        try:
            return Token.objects.get(key=token)
        except Token.DoesNotExist:
            return None

    def post(self, request, *args, **kwargs):
        token = request.data.get('token')
        sattus_code = status.HTTP_200_OK
        data = {}
        if token:
            instance = self.get_object(token)
            if not instance:
                sattus_code = status.HTTP_403_FORBIDDEN

            serializer = self.get_serializer(instance)
            data = serializer.data

        return Response(data, status=sattus_code)
