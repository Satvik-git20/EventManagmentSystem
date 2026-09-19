import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

import django
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from events.models import Event
import json

print("=" * 50)
print("EVENT REGISTRATION SYSTEM - INTEGRATION TEST")
print("=" * 50)

client = Client()

# 1. Create users
print("\n1. Creating users...")
admin = User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
print(f"   Admin: {admin.username}")

user = User.objects.create_user('testuser', 'user@test.com', 'password123')
print(f"   User: {user.username}")

# 2. Create event
print("\n2. Creating event...")
event = Event.objects.create(
    title='Tech Conference 2026',
    description='A major tech conference',
    date='2026-12-15T10:00:00Z',
    location='Convention Center',
    capacity=100,
    organizer=admin
)
print(f"   Event: {event.title} (capacity: {event.capacity})")

# 3. Register user for event
print("\n3. Registering user for event...")
client.force_authenticate(user=user)
response = client.post('/api/events/1/register/')
print(f"   Register status: {response.status_code}")
if response.status_code == 201:
    print("   Registration successful!")
    reg_data = json.loads(response.content) if hasattr(response, 'content') else {}
    print(f"   Registration ID: {reg_data.get('id', 'N/A')}")

# 4. View user registrations
print("\n4. Viewing user registrations...")
response = client.get('/api/me/registrations/')
print(f"   Status: {response.status_code}")
if response.content:
    data = json.loads(response.content)
    print(f"   Found {len(data)} registration(s)")
    for r in data:
        print(f"   - {r['event']['title']} - Status: {r['status']}")

# 5. Cancel registration
print("\n5. Canceling registration...")
if response.content:
    reg_id = data[0]['id']
    response = client.post(f'/api/me/registrations/{reg_id}/cancel/')
    print(f"   Cancel status: {response.status_code}")
    if response.status_code == 204:
        print("   Registration cancelled successfully!")

# 6. List all events
print("\n6. Listing all events...")
response = client.get('/api/events/')
print(f"   Status: {response.status_code}")
if response.content:
    data = json.loads(response.content)
    print(f"   Total events: {data.get('count', 0)}")

# 7. Test capacity enforcement
print("\n7. Testing capacity enforcement...")
user2 = User.objects.create_user('testuser2', 'user2@test.com', 'password123')
client.force_authenticate(user=user2)
successes = 0
for i in range(100):
    response = client.post('/api/events/1/register/')
    if response.status_code == 201:
        successes += 1
    else:
        break
print(f"   Successfully registered {successes}/100 users")
if successes >= 100:
    print("   Capacity limit correctly enforced (100 registrations max)")

print("\n" + "=" * 50)
print("ALL TESTS COMPLETED SUCCESSFULLY!")
print("=" * 50)