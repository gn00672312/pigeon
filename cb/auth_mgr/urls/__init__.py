from .base import urlpatterns
import django
from django.conf import settings
django.setup()


if getattr(settings, "USE_API_TOKEN", None):
    from .token import urlpatterns as token_url_pattern
    urlpatterns = urlpatterns + token_url_pattern

if getattr(settings, "USE_API_JWT", None):
    from .jwt import urlpatterns as jwt_url_pattern
    urlpatterns = urlpatterns + jwt_url_pattern

from .api import urlpatterns as api_url_pattern
urlpatterns = urlpatterns + api_url_pattern

app_name = 'cb_auth_mgr'

__all__ = ["urlpatterns"]
