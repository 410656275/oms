from functools import wraps
from django.http import JsonResponse
from utils.pyutil import api


# from django.views.decorators.http import require_http_methods
# /usr/lib/python3.6/site-packages/django/views/decorators/http.py
# @require_http_methods(["GET", "POST"])
def require_methods(methods):
    def decorator(f):
        @wraps(f)
        def wrapper(request, *args, **kwargs):
            if request.method not in methods:
                data, status = api(405)
                return JsonResponse(data, status=status)
            return f(request, *args, **kwargs)
        return wrapper
    return decorator

require_get = require_methods(['GET'])
require_post = require_methods(['POST'])


def support_fmts(fmts):
    def decorator(f):
        @wraps(f)
        def wrapper(request, *args, **kwargs):
            for k, v in kwargs.items():
                if k == 'fmt' and v not in fmts:
                    data, status = api(501)
                    return JsonResponse(data, status=status)
            return f(request, *args, **kwargs)
        return wrapper
    return decorator

support_html = support_fmts(['.html'])
support_json = support_fmts(['.json', ''])


def is_superuser(f):
    @wraps(f)
    def wrapper(request, *args, **kwargs):
        if request.session['user_is_superuser'] != 1:
            data, status = api(403)
            return JsonResponse(data, status=status)
        return f(request, *args, **kwargs)
    return wrapper
