# @version 20170804


import re
import time
import traceback
import subprocess
from utils.datadict import http_status


def is_none_or_empty(*args):
    return is_none(*args) or is_empty(*args)


def is_none(*args):
    result = False

    for arg in args:
        if arg is None:
            result = True
            break

    return result


# is_empty doesn't cover is_none
def is_empty(*args):
    result = False

    for arg in args:
        if arg is None:
            continue
        else:
          arg = arg.strip()
          if arg in ['', 'null', 'undefined', ',']:
              result = True
              break

    return result


# is_int doesn't cover is_empty
def is_int(*args):
    result = True

    for arg in args:
        try:
            if arg.strip() != '':
                int(arg)
        except ValueError:
            result = False
            break

    return result


def is_valid_ip(ip):
    pieces = ip.split('.')
    if len(pieces) != 4:
        return False
    try:
        return all(0 <= int(x) < 256 for x in pieces)
    except ValueError:
        return False


def is_valid_ip_(ip):
    pattern = re.compile('^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
    result = pattern.match(ip)

    return True if result else False


def is_worst_password(password):
    # if password in datadict.WORST_PASSWORD_LIST:
    #     return True

    if len(password) < 6:
        return True

    if (password.isdigit() or password.isalpha()):
        return True
    else:
        return False


def exec_cmd(cmd):
    try:
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        )
        returncode = p.wait()
        if returncode == 0:
            stdoutdata = p.communicate()[0].strip()
            result = (returncode, stdoutdata)
        else:
            stderrdata = p.communicate()[1].strip()
            result = (returncode, stderrdata)
    except KeyboardInterrupt:
        raise
    except:
        result = (-1, traceback.format_exc())

    return result


def exec_cmd_with_timeout(cmd, secs=10):
    try:
        is_timeout = False
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        )
        begin_time = time.time()
        while True:
            returncode = p.poll()
            if returncode is not None:
                break
            elapsed_time = time.time() - begin_time
            if elapsed_time > secs:
                is_timeout = True
                p.terminate()
                result = (-2, 'Request timeout')
        if not is_timeout:
            if returncode == 0:
                stdoutdata = p.communicate()[0].strip()
                result = (returncode, stdoutdata)
            else:
                stderrdata = p.communicate()[1].strip()
                result = (returncode, stderrdata)
    except KeyboardInterrupt:
        raise
    except:
        result = (-1, traceback.format_exc())

    return result


def api(status, reason=None, data=None, **kwargs):
    if reason is None:
        reason = http_status[status]

    new_data = {
        'status': status,
        'reason': reason,
    }

    if data is not None:
        new_data.update(data)

    if status == 200:
        new_data.update(kwargs)

    return (new_data, status)


'''
{% if not pg.is_first %} href="?page={{ pg.first }}"
{% if pg.has_prev %} href="?page={{ pg.prev }}"

{% for x in pg.pages %}
  {% if x != pg.page %}
    href="?page={{ x }} {{ x }}
  {% else %}
    {{ x }}

{% if pg.has_next %} href="?page={{ pg.next }}"
{% if not pg.is_last %} href="?page={{ pg.last }}"
'''
def get_paginator(page, size, total):
    first = 1
    prev = page - 1
    next = page + 1
    last = int((total - 1) / size) + 1

    is_first = True if page == first else False
    has_prev = True if first <= prev <= last else False
    has_next = True if first <= next <= last else False
    is_last = True if page == last else False

    pages = range(1, last + 1)
    pages = [x for x in pages[:] if (page - 10) < x < (page + 10)]

    paginator = {
        'page': page,
        'size': size,
        'total': total,

        'first': first,
        'prev': prev,
        'next': next,
        'last': last,

        'is_first': is_first,
        'has_prev': has_prev,
        'has_next': has_next,
        'is_last': is_last,

        'pages': pages,
    }

    return paginator
