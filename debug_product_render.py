import os
import django
from django.test import RequestFactory
from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from products import views
from users.models import User

def add_session(request):
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session.save()

def debug_view():
    slug = "premium-beef-cuts"
    print(f"Testing view for slug: {slug}")

    factory = RequestFactory()
    request = factory.get(f'/product/{slug}/')
    
    # Mock user
    request.user = User.objects.first()
    if not request.user:
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()
        
    # Add session
    add_session(request)
    
    print("Calling product_detail view...")
    try:
        response = views.product_detail(request, slug=slug)
        print(f"Response Status Code: {response.status_code}")
        if response.status_code == 200:
            print("View success! Content length:", len(response.content))
        else:
            print("View returned unexpected status code.")
    except Exception as e:
        print("View FAILED!")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_view()
