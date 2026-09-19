from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=200)
    capacity = models.IntegerField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def clean(self):
        super().clean()
        if self.date and self.date < timezone.now():
            raise ValidationError({'date': 'Event date cannot be in the past.'})
        if self.capacity is not None and self.capacity <= 0:
            raise ValidationError({'capacity': 'Capacity must be greater than zero.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def available_spots(self):
        confirmed_count = self.registrations.filter(status='confirmed').count()
        return max(0, self.capacity - confirmed_count)

    @property
    def is_full(self):
        return self.available_spots == 0


class Registration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registrations')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    registered_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        default='confirmed',
        choices=[
            ('confirmed', 'Confirmed'),
            ('cancelled', 'Cancelled'),
        ]
    )

    class Meta:
        unique_together = ['user', 'event']

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"
