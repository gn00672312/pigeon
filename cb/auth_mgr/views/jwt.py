from rest_framework import status
from rest_framework.response import Response
from datetime import datetime

from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.views import (
    ObtainJSONWebToken,
    VerifyJSONWebToken,
    RefreshJSONWebToken
)
from ..serializers.jwt import (
    JSONWebTokenSerializer,
    RefreshJSONWebTokenSerializer,
    VerifyJSONWebTokenSerializer
)

jwt_response_payload_handler = api_settings.JWT_RESPONSE_PAYLOAD_HANDLER


# Create your views here.
class ObtainJWT(ObtainJSONWebToken):

    serializer_class = JSONWebTokenSerializer

    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = self.get_serializer(data=data)

        if serializer.is_valid():
            user = serializer.object.get('user') or request.user
            token = serializer.object.get('token')
            response_data = jwt_response_payload_handler(token, user, request)
            response = Response(response_data)

            if api_settings.JWT_AUTH_COOKIE:
                expiration = (datetime.utcnow() +
                              api_settings.JWT_EXPIRATION_DELTA)
                response.set_cookie(api_settings.JWT_AUTH_COOKIE,
                                    token,
                                    expires=expiration,
                                    httponly=True)
            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyJWT(VerifyJSONWebToken):
    """
    API View that checks the veracity of a token, returning the token if it
    is valid.
    """
    serializer_class = VerifyJSONWebTokenSerializer


class RefreshJWT(RefreshJSONWebToken):
    """
    API View that returns a refreshed token (with new expiration) based on
    existing token
    If 'orig_iat' field (original issued-at-time) is found, will first check
    if it's within expiration window, then copy it to the new token
    """
    serializer_class = RefreshJSONWebTokenSerializer


obtain_jwt = ObtainJWT.as_view()
refresh_jwt = RefreshJWT.as_view()
verify_jwt = VerifyJWT.as_view()
