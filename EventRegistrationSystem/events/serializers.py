from rest_framework import serializers
from .models import Event, Registration


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'title', 'description', 'date', 'location', 'capacity', 'organizer', 'created_at']


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registration
        fields = ['id', 'user', 'event', 'registered_at', 'status']
        read_only_fields = ['user', 'registered_at', 'status']