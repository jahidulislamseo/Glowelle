import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Create or update the default superuser from .env credentials'

    def handle(self, *args, **kwargs):
        User = get_user_model()

        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'Jahidulf1')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Jahidul90')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')

        user, created = User.objects.get_or_create(username=username)
        user.set_password(password)
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        # Use update_fields to bypass any signals that might reset flags
        user.save(update_fields=['password', 'email', 'is_staff', 'is_superuser', 'is_active'])

        if created:
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" updated.'))
