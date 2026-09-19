from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_organizer = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=20, blank=True)
    organization_name = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.user.username} - {'Organizer' if self.is_organizer else 'User'}"