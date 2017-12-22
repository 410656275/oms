# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
import hashlib
import logging
import os
import time
import traceback
import uuid
try: import simplejson as json
except ImportError: import json
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import SuspiciousOperation
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
import chardet
from project.decorators import is_superuser
from project.decorators import require_get
from project.decorators import require_post
from project.decorators import support_json
from utils import pyutil
from utils.pyutil import api
from sql.models import Sql
from sql.models import SqlAttachment
from sql.models import Database
from sql import sqlutil
from sql import tasks


logger = logging.getLogger(__name__)


# Status
class S(object):
    CREATED = 0
    DELIVERED = 1
    UPDATED = 2
    ACCEPTED = EXCUTING = 3
    REPLIED = FINISHED = 4
    ARCHIVED = 5
    DELETED = 6


def for_add_sql(request, fmt=None):
    recipient_to = '{0},{1} <{2}>'.format(
        settings.OPS_MAIL,
        request.session['user_display_name'],
        request.session['user_email'],
    )

    mails = []
    users = User.objects.filter(
        is_active=1, groups__name='mailing_list'
    ).order_by('email')
    for user in users:
        user_display_name = user.first_name
        if user.first_name == '':
            user_display_name = user.username
        mails.append({
            'address': '{0} <{1}>'.format(
                user_display_name, user.email
            )
        })
    mails = json.dumps(mails, ensure_ascii=False)

    databases = Database.objects.filter(
        is_deleted=0
    ).order_by('-code')
    x = [{
        'id': o.code,
        'name': o.name,
        'is_selected': o.is_selected,
    } for o in databases]

    data = {
        'recipient_to': recipient_to,
        'mails': mails,
        'databases': x,
    }

    if fmt == '.html':
        return render(request, 'sql/for_add_sql.html', data)
    else:
        data, status = api(200, data=data)
        return JsonResponse(data, status=status)


@require_post
@support_json
def add_sql(request):
    recipient_to = request.POST.get('recipient_to')
    recipient_cc = request.POST.get('recipient_cc')
    subject = request.POST.get('subject')
    databases = request.POST.getlist('databases')
    attachments = request.FILES.getlist('attachments')
    content = request.POST.get('content')

    if pyutil.is_none_or_empty(recipient_to, subject, content):
        raise SuspiciousOperation

    creator = User.objects.filter(
        id=request.session['user_id']
    ).get()

    with transaction.atomic():
        sql = Sql(
            recipient_to=recipient_to,
            recipient_cc=recipient_cc,
            subject=subject,
            databases=','.join(databases),
            content=content,
            status=S.DELIVERED,
            creator=creator,
        )
        sql.save()

        file_size_limit = 1024 * 1024 * 100
        namespace = os.path.join(
            'sql', str(uuid.uuid4()), time.strftime('%Y%m%dT%H%M%S')
        )

        for file in attachments:
            if file.size > file_size_limit:
                logger.error('file_size {0}'.format(file.size))
                logger.error('file_size_limit {0}'.format(
                    file_size_limit
                ))
                raise Exception('file_size > file_size_limit')

            file_name = file.name
            file_size = file.size
            file_type = file.content_type
            file_path = os.path.join(namespace, file_name)
            file_parent_path = os.path.join(
                settings.DATA_DIR, namespace
            )
            file_absolute_path = os.path.join(
                file_parent_path, file_name
            )
            logger.info((
                'Attachment: '
                'file_name is {0}, '
                'file_size is {0}, '
                'file_type is {0}, '
                'file_path is {0}, '
                'file_parent_path is {0}, '
                'file_absolute_path is {0}').format(
                file_name,
                file_size,
                file_type,
                file_path,
                file_parent_path,
                file_absolute_path,
            ))

            if not os.path.exists(os.path.join(file_parent_path)):
                os.makedirs(os.path.join(file_parent_path))

            with open(file_absolute_path, 'wb+') as f:
                for chunk in file.chunks():
                    f.write(chunk)

            m = hashlib.md5()
            with open(file_absolute_path, 'rb') as f:
                while True:
                    buf = f.read(10240)
                    if not buf: break
                    m.update(buf)
            file_md5sum = m.hexdigest()
            logger.info('file_md5sum {0}'.format(file_md5sum))

            attachment = SqlAttachment(
                sql=sql,
                file_name=file_name,
                file_size=file_size,
                file_type=file_type,
                file_path=file_path,
                file_md5sum=file_md5sum,
            )
            attachment.save()

    tasks.send_mail_when_add_or_update_sql.delay(sql.id)

    data, status = api(200)
    return JsonResponse(data, status=status)


@is_superuser
@require_get
def delete_sql(request):
    id = request.GET.get('id')

    if pyutil.is_none_or_empty(id):
        raise SuspiciousOperation

    with_logical_delete = True

    if with_logical_delete:
        with transaction.atomic():
            Sql.objects.filter(id=id).update(
                is_deleted=1, status=S.DELETED
            )
            SqlAttachment.objects.filter(
                sql__id=id
            ).update(is_deleted=1)
    else:
        with transaction.atomic():
            sql = Sql.objects.filter(id=id).get()

            file_paths = SqlAttachment.objects.filter(
                sql=sql
            ).values_list(
                'file_path', flat=True
            )
            for file_path in file_paths:
                sqlutil.delete_file(file_path)
            SqlAttachment.objects.filter(sql=sql).delete()

            sql.delete()


    data, status = api(200)
    return JsonResponse(data, status=status)


@require_get
def for_update_sql(request, fmt=None):
    id = request.GET.get('id')

    if pyutil.is_none_or_empty(id) or not pyutil.is_int(id):
        raise SuspiciousOperation

    sql = Sql.objects.filter(id=id).get()

    if (sql.creator.id != request.session['user_id'] or
        sql.status not in [S.DELIVERED, S.UPDATED, S.EXCUTING]):
        data, status = api(403)
        return JsonResponse(data, status=status)

    mails = []
    users = User.objects.filter(
        is_active=1, groups__name='mailing_list'
    ).order_by('email')
    for user in users:
        user_display_name = user.first_name
        if user.first_name == '':
            user_display_name = user.username
        mails.append({
            'address': '{0} <{1}>'.format(
                user_display_name, user.email
            )
        })
    mails += [
        {'address': x}
        for x in sql.recipient_to.split(',')
        if x != ''
    ]
    mails += [
        {'address': x}
        for x in sql.recipient_cc.split(',')
        if x != ''
    ]
    mails = json.dumps(mails, ensure_ascii=False)

    x = []
    databases = Database.objects.filter(
        is_deleted=0
    ).order_by('-code')
    for database in databases:
        is_selected = 0
        if database.code in sql.databases.split(','):
            is_selected = 1
        x.append({
            'id': database.code,
            'name': database.name,
            'is_selected': is_selected,
        })

    attachments = SqlAttachment.objects.filter(sql=sql)
    y = [{
        'id': o.id,
        'name': o.file_name,
    } for o in attachments]

    z = {
        'id': sql.id,
        'recipient_to': sql.recipient_to,
        'recipient_cc': sql.recipient_cc,
        'subject': sql.subject,
        'databases': x,
        'attachments': y,
        'content': sql.content,
    }

    data = {
        'sql': z,
        'mails': mails,
    }

    if fmt == '.html':
        return render(request, 'sql/for_update_sql.html', data)
    else:
        data, status = api(200, data=data)
        return JsonResponse(data, status=status)


@require_post
def update_sql(request):
    id = request.POST.get('id')
    recipient_to = request.POST.get('recipient_to')
    recipient_cc = request.POST.get('recipient_cc')
    subject = request.POST.get('subject')
    databases = request.POST.getlist('databases')
    attachments = request.FILES.getlist('attachments')
    content = request.POST.get('content')

    if (pyutil.is_none_or_empty(id, recipient_to) or
        pyutil.is_none_or_empty(subject, content) or
        not pyutil.is_int(id)):
        raise SuspiciousOperation

    sql = Sql.objects.filter(id=id).get()

    if (sql.creator.id != request.session['user_id'] or
        sql.status not in [S.DELIVERED, S.UPDATED, S.EXCUTING]):
        data, status = api(403)
        return JsonResponse(data, status=status)

    with transaction.atomic():
        sql.recipient_to = recipient_to
        sql.recipient_cc = recipient_cc
        sql.subject = subject
        sql.databases = ','.join(databases)
        sql.content = content
        sql.status = S.UPDATED
        sql.save()

        if len(attachments) > 0:
            file_paths = SqlAttachment.objects.filter(
                sql=sql
            ).values_list(
                'file_path', flat=True
            )
            for file_path in file_paths:
                sqlutil.delete_file(file_path)
            SqlAttachment.objects.filter(sql=sql).delete()

        file_size_limit = 1024 * 1024 * 100
        namespace = os.path.join(
            'sql', str(uuid.uuid4()), time.strftime('%Y%m%dT%H%M%S')
        )

        for file in attachments:
            if file.size > file_size_limit:
                logger.error('file_size {0}'.format(file.size))
                logger.error('file_size_limit {0}'.format(
                    file_size_limit
                ))
                raise Exception('file_size > file_size_limit')

            file_name = file.name
            file_size = file.size
            file_type = file.content_type
            file_path = os.path.join(namespace, file_name)
            file_parent_path = os.path.join(
                settings.DATA_DIR, namespace
            )
            file_absolute_path = os.path.join(
                file_parent_path, file_name
            )
            logger.info((
                'Attachment: '
                'file_name is {0}, '
                'file_size is {0}, '
                'file_type is {0}, '
                'file_path is {0}, '
                'file_parent_path is {0}, '
                'file_absolute_path is {0}').format(
                file_name,
                file_size,
                file_type,
                file_path,
                file_parent_path,
                file_absolute_path,
            ))

            if not os.path.exists(os.path.join(file_parent_path)):
                os.makedirs(os.path.join(file_parent_path))

            with open(file_absolute_path, 'wb+') as f:
                for chunk in file.chunks():
                    f.write(chunk)

            m = hashlib.md5()
            with open(file_absolute_path, 'rb') as f:
                while True:
                    buf = f.read(10240)
                    if not buf: break
                    m.update(buf)
            file_md5sum = m.hexdigest()
            logger.info('file_md5sum {0}'.format(file_md5sum))

            attachment = SqlAttachment(
                sql=sql,
                file_name=file_name,
                file_size=file_size,
                file_type=file_type,
                file_path=file_path,
                file_md5sum=file_md5sum,
            )
            attachment.save()

    tasks.send_mail_when_add_or_update_sql.delay(sql.id)

    data, status = api(200)
    return JsonResponse(data, status=status)


@require_get
def get_sql(request, fmt=None):
    id = request.GET.get('id')

    if pyutil.is_none_or_empty(id):
        raise SuspiciousOperation

    sql = Sql.objects.filter(id=id).get()

    creator_name = ''
    creator = sql.creator
    if creator is not None:
        creator_name = creator.first_name
        if creator.first_name == '':
            creator_name = creator.username

    executor_name = ''
    executor = sql.executor
    if executor is not None:
        executor_name = executor.first_name
        if executor.first_name == '':
            executor_name = executor.username

    attachments = []
    for attachment in sql.sqlattachment_set.order_by('file_name'):
        attachments.append({
            'id': attachment.id,
            'file_name': attachment.file_name,
            'file_path': attachment.file_path,
            'is_sql_file': attachment.is_sql_file,
        })

    x = {
        'id': sql.id,
        'subject': sql.subject,
        'databases': sql.databases,
        'created_at': sql.fmt_created_at,
        'updated_at': sql.fmt_updated_at,
        'finished_at': sql.fmt_finished_at,
        'recipient_to': sql.recipient_to,
        'recipient_cc': sql.recipient_cc,
        'attachments': attachments,
        'content': sql.content,
        'reply': sql.reply,
        'creator_name': creator_name,
        'executor_name': executor_name,
    }

    data = {'sql': x}

    if fmt == '.html':
        return render(request, 'sql/get_sql.html', data)
    else:
        data, status = api(200, data=data)
        return JsonResponse(data, status=status)


def get_sql_list(request, fmt=None):
    page = request.GET.get('page', '1')
    size = request.GET.get('size', '10')
    keyword = request.GET.get('keyword')

    if pyutil.is_empty(page, size) or not pyutil.is_int(page, size):
        raise SuspiciousOperation

    page, size = int(page), int(size)

    offset = (page - 1) * size
    if offset < 0:
        offset = 0
    limit = size

    query = None

    if keyword is not None and keyword.strip() != '':
        keyword = keyword.strip()
        query_id = Q(id__icontains=keyword)
        if keyword.startswith('#') and keyword[1:].isdigit():
            query_id = Q(id__exact=keyword[1:])
        query_recipient_to = Q(recipient_to__icontains=keyword)
        query_recipient_cc = Q(recipient_cc__icontains=keyword)
        query_subject = Q(subject__icontains=keyword)
        query_databases = Q(databases__icontains=keyword)
        query_content = Q(content__icontains=keyword)
        query_reply = Q(reply__icontains=keyword)
        query_keyword = (
            query_id |
            query_recipient_to |
            query_recipient_cc |
            query_subject |
            query_databases |
            query_content |
            query_reply
        )
        if query is not None:
            query = query & query_keyword
        else:
            query = query_keyword
    else:
        keyword = ''

    if query is None:
        total = Sql.objects.count()
        sqls = Sql.objects.order_by(
            '-id'
        ).prefetch_related(
            'sqlattachment_set'
        )[offset:offset+limit]
    else:
        total = Sql.objects.filter(query).count()
        sqls = Sql.objects.filter(query).order_by(
            '-id'
        ).prefetch_related(
            'sqlattachment_set'
        )[offset:offset+limit]

    x = []
    for sql in sqls:
        creator = sql.creator
        creator_id = ''
        if creator is not None:
            creator_id = creator.id
        creator_name = ''
        if creator is not None:
            creator_name = creator.first_name
            if creator.first_name == '':
                creator_name = creator.username

        attachment_count = sql.sqlattachment_set.count()

        has_show_perm = 1
        has_edit_perm = 0
        has_accept_perm = 0
        has_reply_perm = 0
        has_delete_perm = 0
        has_archive_perm = 0
        has_star_perm = 0
        has_unstar_perm = 0
        if (creator_id == request.session.get('user_id') and
            sql.status in [S.DELIVERED, S.UPDATED, S.EXCUTING]):
            has_edit_perm = 1
        if request.session.get('user_is_superuser'):
            if sql.status in [S.DELIVERED, S.UPDATED]:
                has_accept_perm = 1
            if sql.status in [S.EXCUTING, S.FINISHED]:
                has_reply_perm = 1
            if sql.status not in [S.ARCHIVED, S.DELETED]:
                has_delete_perm = 1
            if (sql.status == S.FINISHED and
                sql.status not in [S.ARCHIVED, S.DELETED]):
                has_archive_perm = 1
            has_star_perm = 1
            has_unstar_perm = 1

        x.append({
            'id': sql.id,
            'is_starred': sql.is_starred,
            'recipient_to': sql.recipient_to,
            'recipient_cc': sql.recipient_cc,
            'subject': sql.subject,
            'databases': sql.databases,
            'attachment_count': attachment_count,
            'created_at': sql.fmt_created_at,
            'finished_at': sql.fmt_finished_at,
            'status': sql.status,
            'creator_id': creator_id,
            'creator_name': creator_name,
            'is_deleted': sql.is_deleted,
            'user_perm': {
                'has_show_perm': has_show_perm,
                'has_edit_perm': has_edit_perm,
                'has_accept_perm': has_accept_perm,
                'has_reply_perm': has_reply_perm,
                'has_delete_perm': has_delete_perm,
                'has_archive_perm': has_archive_perm,
                'has_star_perm': has_star_perm,
                'has_unstar_perm': has_unstar_perm,
            }
        })

    pg = pyutil.get_paginator(page, size, total)

    data = {
        'sqls': x,
        'pg': pg,
        'keyword': keyword,
    }

    if fmt == '.html':
        return render(request, 'sql/get_sql_list.html', data)
    else:
        data, status = api(200, data=data)
        return JsonResponse(data, status=status)


@require_get
def get_sql_attachment(request, fmt=None):
    id = request.GET.get('id')

    if pyutil.is_none_or_empty(id):
        raise SuspiciousOperation

    attachment = SqlAttachment.objects.filter(id=id).get()
    if attachment is not None:
        if attachment.is_sql_file:
            file_absolute_path = os.path.join(
                settings.DATA_DIR, attachment.file_path
            )
            #
            # UnicodeDecodeError: 'utf-8' codec can't decode \
            # byte 0xb6 in position 3: invalid start byte
            #
            # Welcome other encodings, not only encoding='utf-8'
            #
            # try:
            #     with open(file_absolute_path, 'r') as f:
            #         content = f.read()
            # except:
            #     logger.error(traceback.format_exc())
            #     content = 'Format Unsupported'
            #
            try:
                with open(file_absolute_path, 'rb') as f:
                    content = f.read()
                    charset = chardet.detect(content)
                    logger.info('{} {}'.format(
                        file_absolute_path, charset
                    ))
                    try:
                        content = content.decode(charset['encoding'])
                    except:
                        logger.error(traceback.format_exc())
                        content = content.decode('utf-8')
            except:
                logger.error(traceback.format_exc())
                content = 'Format Unsupported'


        else:
            content = 'Format Unsupported'

    file_size = attachment.file_size
    if 0 < file_size < 1024 * 1024:
        file_size = '{0:.2f} KiB'.format(
            file_size * 1.0 / 1024
        )
    else:
        file_size = '{0:.2f} MiB'.format(
            file_size * 1.0 / 1024 / 1024
        )

    x = {
        'sql_id': attachment.sql.id,
        'file_name': attachment.file_name,
        'file_path': attachment.file_path,
        'file_size': file_size,
        'content': content,
    }

    data = {'attachment': x}

    if fmt == '.html':
        return render(request, 'sql/get_sql_attachment.html', data)
    else:
        data, status = api(200, data=data)
        return JsonResponse(data, status=status)


@is_superuser
@require_get
def accept_sql(request):
    id = request.GET.get('id')

    if pyutil.is_none_or_empty(id):
        raise SuspiciousOperation

    executor = User.objects.filter(
        id=request.session['user_id']
    ).get()

    Sql.objects.filter(id=id).update(
        status=S.ACCEPTED, executor=executor
    )

    data, status = api(200)
    return JsonResponse(data, status=status)


@is_superuser
@require_get
def for_reply_sql(request, fmt=None):
    id = request.GET.get('id')

    if pyutil.is_none_or_empty(id):
        raise SuspiciousOperation

    sql = Sql.objects.filter(id=id).get()

    mails = []
    users = User.objects.filter(
        is_active=1, groups__name='mailing_list'
    ).order_by('email')
    for user in users:
        user_display_name = user.first_name
        if user.first_name == '':
            user_display_name = user.username
        mails.append({
            'address': '{0} <{1}>'.format(
                user_display_name, user.email
            )
        })
    mails += [
        {'address': x}
        for x in sql.recipient_to.split(',')
        if x != ''
    ]
    mails += [
        {'address': x}
        for x in sql.recipient_cc.split(',')
        if x != ''
    ]
    mails = json.dumps(mails, ensure_ascii=False)

    x = []
    databases = Database.objects.filter(
        is_deleted=0
    ).order_by('-code')
    for database in databases:
        is_selected = 0
        if database.code in sql.databases.split(','):
            is_selected = 1
        x.append({
            'id': database.code,
            'name': database.name,
            'is_selected': is_selected,
        })

    attachments = SqlAttachment.objects.filter(
        sql=sql
    ).order_by('file_name')
    y = [{
        'id': o.id,
        'file_name': o.file_name,
        'file_path': o.file_path,
        'is_sql_file': o.is_sql_file,
    } for o in attachments]

    z = {
        'id': sql.id,
        'recipient_to': sql.recipient_to,
        'recipient_cc': sql.recipient_cc,
        'subject': sql.subject,
        'databases': x,
        'attachments': y,
        'content': sql.content,
        'reply': sql.reply,
    }

    data = {
        'sql': z,
        'mails': mails,
    }

    if fmt == '.html':
        return render(request, 'sql/for_reply_sql.html', data)
    else:
        data, status = api(200, data=data)
        return JsonResponse(data, status=status)


@is_superuser
@require_post
def reply_sql(request):
    id = request.POST.get('id')
    recipient_to = request.POST.get('recipient_to')
    recipient_cc = request.POST.get('recipient_cc')
    subject = request.POST.get('subject')
    databases = request.POST.getlist('databases')
    reply = request.POST.get('reply')

    if (pyutil.is_none_or_empty(id, recipient_to) or
        pyutil.is_none_or_empty(subject, reply) or
        not pyutil.is_int(id)):
        raise SuspiciousOperation

    sql = Sql.objects.filter(id=id).get()
    sql.recipient_to = recipient_to
    sql.recipient_cc = recipient_cc
    sql.subject = subject
    sql.databases = ','.join(databases)
    sql.reply = reply
    sql.status = S.REPLIED
    if sql.finished_at is None:
        sql.finished_at = datetime.datetime.now()
    sql.save()

    tasks.send_mail_when_reply_sql.delay(id)

    data, status = api(200)
    return JsonResponse(data, status=status)


@is_superuser
@require_get
def archive_sql(request):
    id = request.GET.get('id')

    if pyutil.is_none_or_empty(id):
        raise SuspiciousOperation

    Sql.objects.filter(id=id).update(status=S.ARCHIVED)

    data, status = api(200)
    return JsonResponse(data, status=status)


@is_superuser
@require_get
def star_sql(request):
    id = request.GET.get('id')

    if pyutil.is_none_or_empty(id):
        raise SuspiciousOperation

    Sql.objects.filter(id=id).update(is_starred=1)

    data, status = api(200)
    return JsonResponse(data, status=status)


@is_superuser
@require_get
def unstar_sql(request):
    id = request.GET.get('id')

    if pyutil.is_none_or_empty(id):
        raise SuspiciousOperation

    Sql.objects.filter(id=id).update(is_starred=0)

    data, status = api(200)
    return JsonResponse(data, status=status)
