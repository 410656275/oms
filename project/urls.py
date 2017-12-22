"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from app import views as app
from project import views as project
from sql import views as sql


handler400 = 'project.views.handler400'
handler403 = 'project.views.handler403'
handler404 = 'project.views.handler404'
handler500 = 'project.views.handler500'


fmt = '(?P<fmt>|\.json|\.html)'


urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^$', project.index),

    url(r'^test$', project.test),

    url(r'^for_sign_in.html$',
   project.for_sign_in),
    url(r'^sign_in$',
   project.sign_in),
    url(r'^sign_out{0}$'.format(fmt),
   project.sign_out),
    url(r'^for_change_password.html$',
   project.for_change_password),
    url(r'^change_password$',
   project.change_password),
    url(r'^set_language$',
   project.set_language),

    url(r'^get_user_list{0}$'.format(fmt),
       app.get_user_list),

    url(r'^sql/index{0}$'.format(fmt),
           sql.get_sql_list),
    url(r'^sql/for_add_sql{0}$'.format(fmt),
           sql.for_add_sql),
    url(r'^sql/add_sql$',
           sql.add_sql),
    url(r'^sql/delete_sql$',
           sql.delete_sql),
    url(r'^sql/for_update_sql{0}$'.format(fmt),
           sql.for_update_sql),
    url(r'^sql/update_sql$',
           sql.update_sql),
    url(r'^sql/get_sql{0}$'.format(fmt),
           sql.get_sql),
    url(r'^sql/get_sql_list{0}$'.format(fmt),
           sql.get_sql_list),
    url(r'^sql/get_sql_attachment{0}$'.format(fmt),
           sql.get_sql_attachment),
    url(r'^sql/accept_sql$'.format(fmt),
           sql.accept_sql),
    url(r'^sql/for_reply_sql{0}$'.format(fmt),
           sql.for_reply_sql),
    url(r'^sql/reply_sql$',
           sql.reply_sql),
    url(r'^sql/archive_sql$',
           sql.archive_sql),
    url(r'^sql/star_sql$',
           sql.star_sql),
    url(r'^sql/unstar_sql$',
           sql.unstar_sql),
]
