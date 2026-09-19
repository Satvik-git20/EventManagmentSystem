from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import UserProfile


class UserProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_user_profile_creation(self):
        profile = UserProfile.objects.create(user=self.user)
        self.assertEqual(profile.user, self.user)
        self.assertFalse(profile.is_organizer)
        self.assertEqual(str(profile), 'testuser - User')

    def test_user_profile_organizer(self):
        profile = UserProfile.objects.create(user=self.user, is_organizer=True)
        self.assertTrue(profile.is_organizer)
        self.assertEqual(str(profile), 'testuser - Organizer')


class AccountsAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
        }
        self.user_credentials = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
        }

    def test_register_user(self):
        response = self.client.post('/api/accounts/auth/register/', self.register_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_register_user_mismatched_passwords(self):
        data = self.register_data.copy()
        data['password_confirm'] = 'different'
        response = self.client.post('/api/accounts/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_organizer(self):
        data = self.register_data.copy()
        data['username'] = 'organizer'
        data['email'] = 'org@example.com'
        data['is_organizer'] = True
        data['organization_name'] = 'Test Org'
        response = self.client.post('/api/accounts/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='organizer')
        self.assertTrue(user.userprofile.is_organizer)
        self.assertEqual(user.userprofile.organization_name, 'Test Org')

    def test_login_user(self):
        _ = User.objects.create_user(**self.user_credentials)
        response = self.client.post('/api/accounts/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_login_invalid_credentials(self):
        response = self.client.post('/api/accounts/auth/login/', {
            'username': 'testuser',
            'password': 'wrongpass'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_profile_authenticated(self):
        user = User.objects.create_user(**self.user_credentials)
        self.client.force_authenticate(user=user)
        response = self.client.get('/api/accounts/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['username'], 'testuser')

    def test_user_profile_unauthenticated(self):
        response = self.client.get('/api/accounts/profile/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile(self):
        user = User.objects.create_user(**self.user_credentials)
        self.client.force_authenticate(user=user)
        response = self.client.patch('/api/accounts/profile/', {
            'phone_number': '123-456-7890',
            'organization_name': 'New Org'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['phone_number'], '123-456-7890')
        self.assertEqual(response.data['organization_name'], 'New Org')

    def test_logout(self):
        # Register user first to create token
        self.client.post('/api/accounts/auth/register/', self.register_data, format='json')
        response = self.client.post('/api/accounts/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data['token']

        # Use token to authenticate
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        response = self.client.post('/api/accounts/auth/logout/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Token should be deleted
        from rest_framework.authtoken.models import Token
        self.assertFalse(Token.objects.filter(user__username='testuser').exists())
