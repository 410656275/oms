# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
import re
import time
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from utils.pyutil import api


logger = logging.getLogger(__name__)


# // request.POST["key"] returns only the last value of a list
# https://code.djangoproject.com/ticket/1130
# https://docs.djangoproject.com/en/1.11/ref/request-response/
class StripMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response


    def __call__(self, request):
        # logger.info('strip before {0}'.format(request.POST))

        self.process_request(request)

        # logger.info('strip after {0}'.format(request.POST))

        response = self.get_response(request)

        return response


    def process_request(self, request):
        # request.GET = request.GET.copy()
        request.GET._mutable = True
        for k, v in request.GET.items():
            request.GET[k] = request.GET[k].strip()
        request.GET._mutable = False

        # request.POST = request.POST.copy()
        request.POST._mutable = True
        for k, v in request.POST.items():
            if len(request.POST.getlist(k)) == 1:
                request.POST[k] = request.POST[k].strip()
        request.POST._mutable = False


class LogMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response


    def __call__(self, request):
        self.process_request(request)

        response = self.get_response(request)

        self.process_response(request, response)

        return response


    def process_request(self, request):
        self.begin_time = time.time()

        username = request.session.get(
            'user_display_name', 'anonymous'
        )
        ip = request.META.get('HTTP_X_FORWARDED_FOR', None)
        if ip:
            ip = ip.split(',')
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        content_type = request.META['CONTENT_TYPE']

        logger.info('{0} - {1} - {2} - {3} - {4}'.format(
            username,
            ip,
            request.method,
            content_type,
            request.get_full_path(),
        ))
        # logger.info(request.body)

        # application/x-www-form-urlencoded, multipart/form-data
        # application/json, text/plain
        form_type = 'application/x-www-form-urlencoded'
        update_user_password = '/api/auth/update_user_password'
        if ((content_type.startswith('application/json') or
            content_type.startswith(form_type)) and
            not request.path_info.startswith('/api/auth/login') and
            not request.path_info.startswith(update_user_password)):
                logger.info('request.body {0}'.format(request.body))


    def process_response(self, request, response):
        logger.info('response.status_code {0}'.format(
            response.status_code
        ))
        # application/json
        # text/html; charset=utf-8
        # logger.info('response.content_type {0}'.format(
        #     response['Content-Type']
        # ))
        if response['Content-Type'] == 'application/json':
            if len(response.content) <= 10240:
                logger.info('response.content {0}'.format(
                    response.content
                ))
            else:
                logger.info('response.content too large, skipped')

        elapsed_time = time.time() - self.begin_time
        logger.info('request.time {0} {1:.3f}s'.format(
            request.get_full_path(), elapsed_time
        ))



class LoginRequiredMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

        self.url_white_list = tuple(
            re.compile(x)
            for x in settings.URL_WHITE_LIST
        )


    def __call__(self, request):
        has_perm = self.process_request(request)

        if not has_perm:
            if (request.path_info.endswith('.html') or
                request.path_info == '/'):
                return redirect('/for_sign_in.html')
            else:
                data, status = api(403)
                return JsonResponse(data, status=status)

        response = self.get_response(request)

        return response


    # Return JsonResponse doesn't work here
    def process_request(self, request):
        has_perm = True
        if 'user_username' not in request.session:
            is_url_in_white_list = False
            for url in self.url_white_list:
                if url.match(request.path):
                    is_url_in_white_list = True
            if not is_url_in_white_list:
                has_perm = False

        return has_perm
