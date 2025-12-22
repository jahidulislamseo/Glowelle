import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    print("Setting up Django...")
    django.setup()
    print("Django setup success.")
    
    print("Running system checks...")
    from django.core.management import call_command
    call_command('check')
    print("System check success.")
    
    print("Importing allauth...")
    import allauth
    print("allauth import success.")
    
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
