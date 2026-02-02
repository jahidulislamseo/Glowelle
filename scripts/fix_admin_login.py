import os
import django
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 50)
print("ADMIN LOGIN FIX SCRIPT")
print("=" * 50)

# Check database connection
print(f"\n[OK] Database: {settings.DATABASES['default']['ENGINE']}")
print(f"[OK] DB Name: {settings.DATABASES['default']['NAME']}")

# Delete existing Jahidulf1 if exists
username = "Jahidulf1"
email = "mdjahidulislamf1@gmail.com"
password = "Jahidul90@"

try:
    existing_user = User.objects.get(username=username)
    print(f"\n[WARNING] Found existing user '{username}'. Deleting...")
    existing_user.delete()
    print(f"[OK] Deleted old user")
except User.DoesNotExist:
    print(f"\n[OK] No existing user '{username}' found")

# Create fresh admin user
print(f"\n[CREATING] Creating fresh admin user...")
user = User.objects.create_superuser(
    username=username,
    email=email,
    password=password
)

print(f"[OK] Created user: {user.username}")
print(f"[OK] Email: {user.email}")
print(f"[OK] Is Superuser: {user.is_superuser}")
print(f"[OK] Is Staff: {user.is_staff}")
print(f"[OK] Is Active: {user.is_active}")

# Verify password
from django.contrib.auth import authenticate
test_auth = authenticate(username=username, password=password)
if test_auth:
    print(f"\n[SUCCESS] PASSWORD VERIFICATION: SUCCESS")
    print(f"[SUCCESS] You can now login with:")
    print(f"   Username: {username}")
    print(f"   Password: {password}")
else:
    print(f"\n[FAILED] PASSWORD VERIFICATION: FAILED")
    print(f"[WARNING] Something is wrong with authentication")

print("\n" + "=" * 50)
print("RESTART YOUR SERVER NOW!")
print("=" * 50)

