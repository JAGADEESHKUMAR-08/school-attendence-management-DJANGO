from functools import wraps

from django.conf import settings
from django.http import HttpResponseForbidden
from django.shortcuts import redirect

from .models import User


def role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(settings.LOGIN_URL)
            if getattr(request.user, 'role', None) != role:
                return HttpResponseForbidden('You do not have permission to view this page.')
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
