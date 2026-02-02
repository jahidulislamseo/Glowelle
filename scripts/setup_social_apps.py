
import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from decouple import config

def setup_social_apps():
    # Get or create the default site
    site, created = Site.objects.get_or_create(domain='127.0.0.1:8000', name='Al Barakah Mart')
    if created:
        print(f"Created default site: {site.domain}")
    else:
        print(f"Using existing site: {site.domain}")

    providers = [
        {
            'provider': 'google',
            'name': 'Google',
            'client_id': config('GOOGLE_CLIENT_ID', default=''),
            'secret': config('GOOGLE_SECRET', default=''),
        },
        {
            'provider': 'facebook',
            'name': 'Facebook',
            'client_id': config('FACEBOOK_APP_ID', default=''),
            'secret': config('FACEBOOK_APP_SECRET', default=''),
        }
    ]

    for p in providers:
        if not p['client_id'] or 'your-' in p['client_id']:
            print(f"Skipping {p['name']}: No valid Client ID found in .env")
            continue

        app, created = SocialApp.objects.get_or_create(
            provider=p['provider'],
            name=p['name'],
            defaults={
                'client_id': p['client_id'],
                'secret': p['secret']
            }
        )
        
        if created:
            app.sites.add(site)
            print(f"Successfully created SocialApp for {p['name']}")
        else:
            app.client_id = p['client_id']
            app.secret = p['secret']
            app.sites.add(site)
            app.save()
            print(f"Updated existing SocialApp for {p['name']}")

if __name__ == '__main__':
    setup_social_apps()
