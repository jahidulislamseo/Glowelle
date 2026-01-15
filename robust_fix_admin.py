import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

email = "mdjahidulislamf1@gmail.com"
username = "Jahidulf1"
password = "Jahidul90@"

print(f"Cleaning up users with email: {email}")
User.objects.filter(email=email).delete()

print(f"Cleaning up users with username: {username}")
User.objects.filter(username=username).delete()

print(f"Creating superuser: {username}")
User.objects.create_superuser(username=username, email=email, password=password)

print("SUCCESS: Admin user created.")
