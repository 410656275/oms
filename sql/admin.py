from django.contrib import admin
from sql.models import Database


class DatabaseAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
        'is_selected',
        'is_deleted',
    )

# admin.site.register(Database)
admin.site.register(Database, DatabaseAdmin)
