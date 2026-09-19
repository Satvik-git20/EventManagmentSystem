from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from .models import Event, Registration
from accounts.models import UserProfile


class EventModelTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username='organizer',
            email='org@example.com',
            password='orgpass123'
        )
        UserProfile.objects.create(user=self.organizer, is_organizer=True)

        self.future_date = timezone.now() + timedelta(days=7)

    def test_event_creation(self):
        event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            date=self.future_date,
            location='Test Location',
            capacity=50,
            organizer=self.organizer
        )
        self.assertEqual(event.title, 'Test Event')
        self.assertEqual(event.capacity, 50)
        self.assertEqual(event.organizer, self.organizer)
        self.assertEqual(event.available_spots, 50)
        self.assertFalse(event.is_full)

    def test_event_past_date_validation(self):
        past_date = timezone.now() - timedelta(days=1)
        event = Event(
            title='Past Event',
            description='Test',
            date=past_date,
            location='Test',
            capacity=10,
            organizer=self.organizer
        )
        with self.assertRaises(Exception):
            event.full_clean()

    def test_event_zero_capacity_validation(self):
        event = Event(
            title='Zero Capacity',
            description='Test',
            date=self.future_date,
            location='Test',
            capacity=0,
            organizer=self.organizer
        )
        with self.assertRaises(Exception):
            event.full_clean()

    def test_event_negative_capacity_validation(self):
        event = Event(
            title='Negative Capacity',
            description='Test',
            date=self.future_date,
            location='Test',
            capacity=-5,
            organizer=self.organizer
        )
        with self.assertRaises(Exception):
            event.full_clean()

    def test_event_available_spots(self):
        event = Event.objects.create(
            title='Test Event',
            description='Test',
            date=self.future_date,
            location='Test',
            capacity=3,
            organizer=self.organizer
        )
        user1 = User.objects.create_user(username='user1', password='pass')
        user2 = User.objects.create_user(username='user2', password='pass')

        Registration.objects.create(user=user1, event=event, status='confirmed')
        self.assertEqual(event.available_spots, 2)

        Registration.objects.create(user=user2, event=event, status='confirmed')
        self.assertEqual(event.available_spots, 1)

    def test_event_is_full(self):
        event = Event.objects.create(
            title='Full Event',
            description='Test',
            date=self.future_date,
            location='Test',
            capacity=1,
            organizer=self.organizer
        )
        user = User.objects.create_user(username='user', password='pass')
        Registration.objects.create(user=user, event=event, status='confirmed')
        self.assertTrue(event.is_full)


class RegistrationModelTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username='organizer',
            email='org@example.com',
            password='orgpass123'
        )
        UserProfile.objects.create(user=self.organizer, is_organizer=True)

        self.user = User.objects.create_user(username='user', password='pass')
        self.event = Event.objects.create(
            title='Test Event',
            description='Test',
            date=timezone.now() + timedelta(days=7),
            location='Test',
            capacity=10,
            organizer=self.organizer
        )

    def test_registration_creation(self):
        registration = Registration.objects.create(
            user=self.user,
            event=self.event,
            status='confirmed'
        )
        self.assertEqual(registration.user, self.user)
        self.assertEqual(registration.event, self.event)
        self.assertEqual(registration.status, 'confirmed')

    def test_unique_registration_constraint(self):
        Registration.objects.create(user=self.user, event=self.event)
        with self.assertRaises(Exception):
            Registration.objects.create(user=self.user, event=self.event)


class EventsAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.organizer = User.objects.create_user(
            username='organizer',
            email='org@example.com',
            password='orgpass123'
        )
        UserProfile.objects.create(user=self.organizer, is_organizer=True)

        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpass123'
        )
        UserProfile.objects.create(user=self.user, is_organizer=False)

        self.event_data = {
            'title': 'Test Event',
            'description': 'Test Description',
            'date': (timezone.now() + timedelta(days=7)).isoformat(),
            'location': 'Test Location',
            'capacity': 50
        }

    def test_list_events_unauthenticated(self):
        response = self.client.get('/api/events/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_events_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/events/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_create_event_as_organizer(self):
        self.client.force_authenticate(user=self.organizer)
        response = self.client.post('/api/events/', self.event_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Test Event')
        self.assertEqual(response.data['organizer'], 'organizer')

    def test_create_event_as_non_organizer(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/events/', self.event_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_event_past_date(self):
        self.client.force_authenticate(user=self.organizer)
        data = self.event_data.copy()
        data['date'] = (timezone.now() - timedelta(days=1)).isoformat()
        response = self.client.post('/api/events/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('date', response.data)

    def test_create_event_zero_capacity(self):
        self.client.force_authenticate(user=self.organizer)
        data = self.event_data.copy()
        data['capacity'] = 0
        response = self.client.post('/api/events/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('capacity', response.data)

    def test_update_own_event(self):
        self.client.force_authenticate(user=self.organizer)
        event = Event.objects.create(**self.event_data, organizer=self.organizer)
        response = self.client.patch(f'/api/events/{event.id}/', {'title': 'Updated Title'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Title')

    def test_update_other_organizer_event(self):
        other_organizer = User.objects.create_user(username='other', password='pass')
        UserProfile.objects.create(user=other_organizer, is_organizer=True)
        event = Event.objects.create(**self.event_data, organizer=other_organizer)

        self.client.force_authenticate(user=self.organizer)
        response = self.client.patch(f'/api/events/{event.id}/', {'title': 'Hacked'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_own_event(self):
        self.client.force_authenticate(user=self.organizer)
        event = Event.objects.create(**self.event_data, organizer=self.organizer)
        response = self.client.delete(f'/api/events/{event.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Event.objects.filter(id=event.id).exists())

    def test_filter_events_by_location(self):
        self.client.force_authenticate(user=self.user)
        data1 = self.event_data.copy()
        data1['location'] = 'New York'
        data2 = self.event_data.copy()
        data2['location'] = 'London'
        Event.objects.create(**data1, organizer=self.organizer)
        Event.objects.create(**data2, organizer=self.organizer)

        response = self.client.get('/api/events/?location=New York')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['location'], 'New York')

    def test_search_events(self):
        self.client.force_authenticate(user=self.user)
        data1 = self.event_data.copy()
        data1['title'] = 'Python Conference'
        data2 = self.event_data.copy()
        data2['title'] = 'Django Workshop'
        Event.objects.create(**data1, organizer=self.organizer)
        Event.objects.create(**data2, organizer=self.organizer)

        response = self.client.get('/api/events/?search=Python')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Python Conference')


class RegistrationAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.organizer = User.objects.create_user(
            username='organizer',
            email='org@example.com',
            password='orgpass123'
        )
        UserProfile.objects.create(user=self.organizer, is_organizer=True)

        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpass123'
        )
        UserProfile.objects.create(user=self.user, is_organizer=False)

        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            date=timezone.now() + timedelta(days=7),
            location='Test Location',
            capacity=2,
            organizer=self.organizer
        )

    def test_register_for_event(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/events/{self.event.id}/register/', format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Registration.objects.count(), 1)
        self.assertEqual(Registration.objects.first().user, self.user)

    def test_register_duplicate(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(f'/api/events/{self.event.id}/register/', format='json')
        response = self.client.post(f'/api/events/{self.event.id}/register/', format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already registered', response.data['error'])

    def test_register_full_event(self):
        user2 = User.objects.create_user(username='user2', password='pass')
        Registration.objects.create(user=self.user, event=self.event, status='confirmed')
        Registration.objects.create(user=user2, event=self.event, status='confirmed')

        self.client.force_authenticate(user=User.objects.create_user(username='user3', password='pass'))
        response = self.client.post(f'/api/events/{self.event.id}/register/', format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('full capacity', response.data['error'])

    def test_list_my_registrations(self):
        self.client.force_authenticate(user=self.user)
        Registration.objects.create(user=self.user, event=self.event, status='confirmed')
        response = self.client.get('/api/me/registrations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_cancel_registration(self):
        self.client.force_authenticate(user=self.user)
        reg = Registration.objects.create(user=self.user, event=self.event, status='confirmed')
        response = self.client.delete(f'/api/me/registrations/{reg.id}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reg.refresh_from_db()
        self.assertEqual(reg.status, 'cancelled')

    def test_cannot_cancel_other_user_registration(self):
        other_user = User.objects.create_user(username='other', password='pass')
        reg = Registration.objects.create(user=other_user, event=self.event, status='confirmed')

        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/me/registrations/{reg.id}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)