import os
import django
from django.core.files import File
from pathlib import Path
import shutil

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User
from django.conf import settings

def set_avatar():
    # Source file (where we downloaded it)
    source_path = Path('theme/static/images/jahidul-islam.webp')
    
    # Target in media
    target_dir = Path(settings.MEDIA_ROOT) / 'profile_pics'
    target_dir.mkdir(parents=True, exist_ok=True)
    target_name = 'jahidul-islam.webp'
    target_path = target_dir / target_name
    
    if not source_path.exists():
        print(f"Error: Source file {source_path} not found.")
        return

    # Copy file to media
    shutil.copy(source_path, target_path)
    print(f"Copied image to {target_path}")

    # Find User
    email = 'mdjahidulislamf1@gmail.com'
    try:
        user = User.objects.get(email=email)
        # Set image field relative to MEDIA_ROOT
        user.image = f'profile_pics/{target_name}'
        user.save()
        print(f"Successfully updated avatar for {user.username} ({user.email})")
    except User.DoesNotExist:
        print(f"User with email {email} not found. Trying to find a superuser...")
        superusers = User.objects.filter(is_superuser=True)
        if superusers.exists():
            user = superusers.first()
            user.image = f'profile_pics/{target_name}'
            user.save()
            print(f"Updated avatar for superuser: {user.username}")
        else:
            print("No superuser found.")

if __name__ == '__main__':
    set_avatar()
