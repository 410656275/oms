# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import base64
import logging
import os
from email.mime.application import MIMEApplication
from django.conf import settings
from django.core.mail import EmailMessage
from sql.models import Sql
from sql.models import SqlAttachment
from celery import shared_task


logger = logging.getLogger(__name__)


@shared_task
def send_mail_when_add_or_update_sql(id):
    logger.info('Sql id {0}'.format(id))

    sql = Sql.objects.filter(id=id).get()

    subject = '[SQL] {0}'.format(sql.subject)
    body = sql.content
    from_email = 'OMS <{0}>'.format(settings.EMAIL_HOST_USER)
    to = sql.recipient_to.split(',')
    cc = sql.recipient_cc.split(',')
    logger.info('Sql id {0}, subject {1}, to {2}, cc {3}'.format(
        id, subject, to, cc
    ))

    if sql.recipient_cc == '':
        message = EmailMessage(subject, body, from_email, to)
    else:
        message = EmailMessage(subject, body, from_email, to, cc=cc)
    message.content_subtype = 'html'

    attachments = SqlAttachment.objects.filter(sql=sql)
    for attachment in attachments:
        with open(os.path.join(
            settings.DATA_DIR, attachment.file_path
        ), 'rb') as f:
            x = MIMEApplication(f.read())
        filename = '=?UTF-8?B?{0}?='.format(
            base64.b64encode(
                attachment.file_path.split('/')[-1].encode('utf-8')
            ).decode()
        )
        logger.info('Sql id {0}, filename {1}'.format(id, filename))
        x.add_header(
            'Content-Disposition',
            'attachment; filename={0}'.format(filename),
        )
        message.attach(x)

    if settings.MAIL_ENABLED:
        message.send()
        logger.info('Sql id {0}, sent mail successfully'.format(id))
    else:
        logger.info('Sql id {0}, cancelled to sent mail'.format(id))




@shared_task
def send_mail_when_reply_sql(id):
    logger.info('Sql id {0}'.format(id))

    sql = Sql.objects.filter(id=id).get()

    subject = 'Re: [SQL] {0}'.format(sql.subject)
    body = (
        '{0}'
        '<p><br><br><br>'
        '-------------------------'
        ' Original '
        '-------------------------'
        '</p>'
        '{1}'
    ).format(sql.reply, sql.content)
    from_email = 'OMS <{0}>'.format(settings.EMAIL_HOST_USER)
    to = sql.recipient_to.split(',')
    cc = sql.recipient_cc.split(',')
    logger.info('Sql id {0}, subject {1}, to {2}, cc {3}'.format(
        id, subject, to, cc
    ))

    if sql.recipient_cc == '':
        message = EmailMessage(subject, body, from_email, to)
    else:
        message = EmailMessage(subject, body, from_email, to, cc=cc)
    message.content_subtype = 'html'

    if settings.MAIL_ENABLED:
        message.send()
        logger.info('Sql id {0}, sent mail successfully'.format(id))
    else:
        logger.info('Sql id {0}, cancelled to sent mail'.format(id))
