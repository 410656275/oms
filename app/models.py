from django.contrib.auth.models import User
from django.db import models


# // Extending the existing User model
# https://docs.djangoproject.com/en/1.11/topics/auth/customizing/


class UserProfile(models.Model):
    id = models.AutoField(primary_key=True)

    ssh_key = models.TextField(null=True)
    has_ssh_key = models.IntegerField(default=1, null=True)
    is_ssh_key_valid = models.IntegerField(default=1, null=True)

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    created_at = models.DateTimeField(
        auto_now_add=True, db_index=True, null=True
    )
    updated_at = models.DateTimeField(
        auto_now=True, db_index=True, null=True
    )

    class Meta:
        db_table = 'user_profile'
