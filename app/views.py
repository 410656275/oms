from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import render
from utils.pyutil import api


def get_user_list(request, fmt=None):
    x = []

    users = User.objects.filter(is_active=1).select_related(
        'userprofile'
    ).order_by('username')
    for user in users:
        ssh_key = 'N/A'
        try:
            ssh_key = user.userprofile.ssh_key
        except ObjectDoesNotExist:
            pass
        x.append({
            'username': user.username,
            'real_name': user.first_name,
            'email': user.email,
            'ssh_key': ssh_key,
        })

    data = {
        'users': x,
    }

    if fmt == '.html':
        return render(request, 'common/get_user_list.html', data)
    else:
        data, status = api(200, data=data)
        return JsonResponse(data, status=status)
