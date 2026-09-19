from rest_framework import serializers
from .models import Event, Registration


class EventSerializer(serializers.ModelSerializer):
    organizer = serializers.ReadOnlyField(source='organizer.username')
    available_spots = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)

    class Meta:
        model = Event
        fields = ['id', 'title', 'description', 'date', 'location', 'capacity', 'organizer', 'created_at', 'available_spots', 'is_full']
        read_only_fields = ['organizer', 'created_at', 'available_spots', 'is_full']

    def validate_date(self, value):
        from django.utils import timezone
        if value < timezone.now():
            raise serializers.ValidationError('Event date cannot be in the past.')
        return value

    def validate_capacity(self, value):
        if value <= 0:
            raise serializers.ValidationError('Capacity must be greater than zero.')
        return value


class RegistrationSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)
    event_date = serializers.DateTimeField(source='event.date', read_only=True)

    class Meta:
        model = Registration
        fields = ['id', 'user', 'event', 'event_title', 'event_date', 'registered_at', 'status']
        read_only_fields = ['user', 'event', 'registered_at', 'status', 'event_title', 'event_date']