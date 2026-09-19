from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import UserProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    is_organizer = serializers.BooleanField(default=False)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    organization_name = serializers.CharField(max_length=200, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'is_organizer', 'phone_number',
            'organization_name'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        is_organizer = validated_data.pop('is_organizer', False)
        phone_number = validated_data.pop('phone_number', '')
        organization_name = validated_data.pop('organization_name', '')
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(
            user=user,
            is_organizer=is_organizer,
            phone_number=phone_number,
            organization_name=organization_name
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'is_organizer', 'phone_number', 'organization_name']
