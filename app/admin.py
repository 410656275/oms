from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from app.models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile


# UserAdmin.list_display = (
#     'username',
#     'email',
#     'first_name',
#     'is_superuser',
#     'is_active',
#     'is_staff',
#     'date_joined',
#     'last_login',
# )
# UserAdmin.inlines = (
#     UserProfileInline,
# )


# class MyUserAdmin(admin.ModelAdmin):
class MyUserAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'is_superuser',
        'is_active',
        'is_staff',
        'date_joined',
        'last_login',
        'has_ssh_key',
        'is_ssh_key_valid',
    )
    inlines = (
        UserProfileInline,
    )
    def has_ssh_key(self, instance):
        return instance.userprofile.has_ssh_key

    def is_ssh_key_valid(self, instance):
        return instance.userprofile.is_ssh_key_valid


admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)
