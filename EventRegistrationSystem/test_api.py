import urllib.request
import json

print("=" * 50)
print("EVENT REGISTRATION SYSTEM - API TESTS")
print("=" * 50)

# Test 1: List events
print("\n1. Listing events from running server...")
try:
    r = urllib.request.urlopen('http://127.0.0.1:8000/api/events/')
    data = json.loads(r.read())
    print(f"   Status: {r.status}")
    print(f"   Events count: {data.get('count', 0)}")
    print("   ✓ PASS" if r.status == 200 else "   ✗ FAIL")
except Exception as e:
    print(f"   ✗ FAIL: {e}")

# Test 2: Admin panel
print("\n2. Checking admin panel...")
try:
    r = urllib.request.urlopen('http://127.0.0.1:8000/admin/')
    print(f"   Status: {r.status}")
    print("   ✓ PASS - Admin panel accessible")
except Exception as e:
    print(f"   ✗ FAIL: {e}")

# Test 3: Account profiles
print("\n3. Checking accounts API...")
try:
    r = urllib.request.urlopen('http://127.0.0.1:8000/api/accounts/profile/')
    data = json.loads(r.read())
    print(f"   Status: {r.status}")
    print(f"   Profile data: {data}")
    print("   ✓ PASS" if r.status == 200 else "   Status code: " + str(r.status))
except Exception as e:
    print(f"   Info: {e}")

print("\n" + "=" * 50)
print("API TESTS COMPLETED")
print("=" * 50)