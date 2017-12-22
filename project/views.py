# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.hashers import make_password
from django.core.exceptions import SuspiciousOperation
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render
from project.decorators import require_post
from project.decorators import support_html
from project.decorators import support_json
from utils import pyutil
from utils.pyutil import api


logger = logging.getLogger(__name__)


def index(request):
    # logger.info('request.path {0}'.format(request.path))
    # logger.info('request.path_info {0}'.format(request.path_info))
    # logger.info('request.get_full_path() {0}'.format(
    #     request.get_full_path()
    # ))

    pieces = request.get_full_path().split('?', 1)
    logger.info('pieces {0}'.format(pieces))

    url = 'sql/index.html'
    if len(pieces) == 2:
        url = 'sql/index.html?{0}'.format(pieces[1])
    logger.info('url {0} -> {1}'.format(pieces, url))

    return redirect(url)


def test(request):
    return render(request, 'common/test.html')


# 400 (Bad Request)
# from django.core.exceptions import SuspiciousOperation
# raise SuspiciousOperation
def handler400(request):
    data, status = api(400)
    return JsonResponse(data, status=status)


# 403 (Forbidden)
# from django.core.exceptions import PermissionDenied
# raise PermissionDenied
def handler403(request):
    data, status = api(403)
    return JsonResponse(data, status=status)


# 404 (Not Found)
# from django.http import Http404
# raise Http404
def handler404(request):
    data, status = api(404)
    return JsonResponse(data, status=status)


# 500 (Internal Server Error)
# raise Exception
def handler500(request):
    data, status = api(500)
    return JsonResponse(data, status=status)


@support_html
def for_sign_in(request, fmt=None):
    return render(request, 'common/for_sign_in.html')


@require_post
def sign_in(request, fmt=None):
    """
    username can be username/email/phone
    """
    username = request.POST.get('username')
    password = request.POST.get('password')

    if pyutil.is_none_or_empty(username, password):
        raise SuspiciousOperation

    status = 403

    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            login(request, user)

            request.session['user_id'] = user.id
            request.session['user_username'] = username
            request.session['user_email'] = user.email
            request.session['user_is_superuser'] = user.is_superuser

            user_display_name = username
            if user.first_name != '':
                user_display_name = user.first_name
            request.session['user_display_name'] = user_display_name
            status = 200

    if fmt == '.html':
        if status == 200:
            return redirect('/')
        else:
            return redirect('/for_sign_in.html')
    else:
        data, status = api(status)
        return JsonResponse(data, status=status)


def sign_out(request, fmt=None):
    if 'user_id' in request.session:
        del request.session['user_id']
    if 'user_username' in request.session:
        del request.session['user_username']
    if 'user_email' in request.session:
        del request.session['user_email']
    if 'user_is_superuser' in request.session:
        del request.session['user_is_superuser']
    if 'user_display_name' in request.session:
        del request.session['user_display_name']

    logout(request)

    if fmt == '.html':
        return redirect('/for_sign_in.html')
    else:
        data, status = api(200)
        return JsonResponse(data, status=status)


@support_html
def for_change_password(request, fmt=None):
    return render(request, 'common/for_change_password.html')


@support_json
@require_post
def change_password(request, fmt=None):
    old_password = request.POST.get('old_password')
    new_password = request.POST.get('new_password')

    if pyutil.is_none_or_empty(old_password, new_password):
        raise SuspiciousOperation

    status = 403

    username = request.session['user_username']
    user = authenticate(username=username, password=old_password)
    if user is not None:
        user.password = make_password(new_password)
        user.save()
        status = 200

    data, status = api(status)
    return JsonResponse(data, status=status)



@support_html
def set_language(request):
    language = request.GET.get('language')

    if pyutil.is_none_or_empty(language):
        raise SuspiciousOperation

    import datetime
    from django.conf import settings
    from django.http import HttpResponseRedirect
    from django.utils.translation import check_for_language

    # print(request.COOKIES)
    # print(settings.LANGUAGE_CODE)
    # print(settings.LANGUAGE_COOKIE_NAME)
    # print(settings.LOCALE_PATHS)

    # language = request.GET.get('language')
    # http_referer = request.META.get('HTTP_REFERER')
    # if not http_referer:
    #     http_referer = '/'

    # response = HttpResponseRedirect(http_referer)
    response = HttpResponseRedirect('/')

    if language and check_for_language(language):
        max_age = 365 * 24 * 60 * 60
        expires = datetime.datetime.strftime(
            datetime.datetime.utcnow() +
            datetime.timedelta(seconds=max_age),
            '%a, %d-%b-%Y %H:%M:%S GMT')
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,
            language, max_age, expires,
        )

    return response
