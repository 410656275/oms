-- Intro
SQL Management



-- Upstream
Django 1.11.3



-- Command
mkdir oms && python -m django startproject project oms



-- Start
python manage.py runserver
python manage.py runserver --insecure



-- Migrate
python manage.py makemigrations
python manage.py migrate



-- Admin
python manage.py createsuperuser
python manage.py changepassword root



-- I18N
python manage.py makemessages
python manage.py makemessages -l zh_Hans
vi locale/zh_Hans/LC_MESSAGES/django.po
python manage.py compilemessages



-- Access
http://127.0.0.1:8000/
http://127.0.0.1:8000/admin/
