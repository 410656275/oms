# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.db import models


# models.TextField defaults to longtext and django.forms.Textarea
# tinytext 255 bytes, text 64 KiB, mediumtext 16 MiB, longtext 4 GiB
class NormalTextField(models.Field):
    def db_type(self, connection):
        return 'mediumtext'


# -- Status
# 0 Created
# 1 Delivered
# 2 Updated
# 3 Accepted (Excuting)
# 4 Replied (Finished)
# 5 Archived
# 6 Deleted
class Sql(models.Model):
    id = models.AutoField(primary_key=True)

    # To, CC, BCC, Subject, Body, Attachment
    recipient_to = models.CharField(max_length=256, null=True)
    recipient_cc = models.CharField(max_length=256, null=True)
    subject = models.CharField(max_length=128, null=True)
    databases = models.CharField(
        max_length=128, null=True, db_column='databazes'
    )
    content = NormalTextField(null=True)
    content_text = NormalTextField(null=True)
    reply = NormalTextField(null=True)
    reply_text = NormalTextField(null=True)

    status = models.IntegerField(default=0, null=True)
    finished_at = models.DateTimeField(null=True)
    is_starred = models.IntegerField(default=0, null=True)

    creator = models.ForeignKey(
        User, related_name='+',
        to_field='id', db_column='creator_id',
        on_delete=models.SET_NULL, null=True,
    )
    executor = models.ForeignKey(
        User, related_name='+',
        to_field='id', db_column='executor_id',
        on_delete=models.SET_NULL, null=True,
    )

    is_deleted = models.IntegerField(default=0, null=True)
    created_at = models.DateTimeField(
        auto_now_add=True, db_index=True, null=True
    )
    updated_at = models.DateTimeField(
        auto_now=True, db_index=True, null=True
    )

    @property
    def fmt_finished_at(self):
        if self.finished_at is None:
            return self.finished_at
        else:
            return self.finished_at.strftime('%Y-%m-%d %H:%M:%S')

    @property
    def fmt_created_at(self):
        return self.created_at.strftime('%Y-%m-%d %H:%M:%S')

    @property
    def fmt_updated_at(self):
        return self.updated_at.strftime('%Y-%m-%d %H:%M:%S')

    class Meta:
        db_table = 'zql'


class SqlAttachment(models.Model):
    id = models.AutoField(primary_key=True)

    file_name = models.CharField(max_length=64, null=True)
    file_size = models.IntegerField(null=True)
    file_type = models.CharField(max_length=128, null=True)
    file_path = models.CharField(max_length=128, null=True)
    file_md5sum = models.CharField(max_length=32, null=True)

    sql = models.ForeignKey(
        'Sql', to_field='id', db_column='zql_id',
        on_delete=models.SET_NULL, null=True,
    )

    is_deleted = models.IntegerField(default=0, null=True)
    created_at = models.DateTimeField(
        auto_now_add=True, db_index=True, null=True
    )
    updated_at = models.DateTimeField(
        auto_now=True, db_index=True, null=True
    )

    @property
    def is_sql_file(self):
        if (self.file_name.endswith('.sql') or
            self.file_type == 'application/sql' or
            self.file_name.endswith('.txt') or
            self.file_type == 'text/plain'):
            return True
        else:
            return False

    class Meta:
        db_table = 'zql_attachment'


class Database(models.Model):
    id = models.AutoField(primary_key=True)

    code = models.CharField(
        max_length=64, unique=True, db_index=True, null=True
    )
    name = models.CharField(max_length=64, null=True)
    is_selected = models.IntegerField(default=0, null=True)

    is_deleted = models.IntegerField(default=0, null=True)
    created_at = models.DateTimeField(
        auto_now_add=True, db_index=True, null=True
    )
    updated_at = models.DateTimeField(
        auto_now=True, db_index=True, null=True
    )

    class Meta:
        db_table = 'databaze'
