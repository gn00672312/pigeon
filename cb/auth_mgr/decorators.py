from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test
from .models import PermissionRepository


def superuser_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is superuser in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_superuser,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def staff_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is staff in, redirecting
    to the log-in page if necessary.
    """
    def _check(u):
        if u.is_authenticated:
            if u.is_superuser:
                return True
            if u.is_staff:
                return True
        return False
    actual_decorator = user_passes_test(
        _check,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def func_required(perm, login_url=None, raise_exception=True):
    """
    Decorator for views that checks whether a user has a permission of app
    auth_mgr (app_label='auth_mgr' set in models, and need to setup
    FUNC_PERMISSION_CONFIG in settings), redirecting to the log-in page if
    necessary. If the raise_exception parameter is given the PermissionDenied
    exception is raised.
    """
    def check_perms(user):
        app_label = PermissionRepository._meta.app_label
        def _bind_app_label(perm):
            return "%s.%s" % (app_label, perm)

        if isinstance(perm, str):
            perms = (_bind_app_label(perm),)
        else:
            perms = [_bind_app_label(p) for p in perm]

        if not user.is_authenticated:
            return False
        # First check if the user has the permission (even anon users)
        if user.has_perms(perms):
            return True
        # In case the 403 handler should be called raise the exception
        if raise_exception:
            raise PermissionDenied
        # As the last resort, show the login form
        return False
    return user_passes_test(check_perms, login_url=login_url)
