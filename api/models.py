import secrets

from django.db import models
from django.utils import timezone

from core.models import User


class ApiAccessToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_tokens')
    key = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    @classmethod
    def issue_for_user(cls, user):
        token, _ = cls.objects.update_or_create(
            user=user,
            defaults={
                'key': secrets.token_hex(32),
                'last_used_at': timezone.now(),
            },
        )
        return token

    def touch(self):
        self.last_used_at = timezone.now()
        self.save(update_fields=['last_used_at'])

    def __str__(self):
        return f'{self.user.username} token'
