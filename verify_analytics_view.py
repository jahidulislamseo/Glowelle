import os
import django
import sys

# Setup
sys.path.append(os.path.abspath('c:/Users/Jahidul-islam/Desktop/all apk and website/al-barakah-mart-django'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth import get_user_model
from core.views import analytics_dashboard

User = get_user_model()

# Create Request
factory = RequestFactory()
request = factory.get('/admin/admin/analytics/')

# Add Session/Auth logic manually since we are unit testing the view directly
middleware = SessionMiddleware(lambda x: None)
middleware.process_request(request)
request.session.save()

# Create/Get Staff User
user, created = User.objects.get_or_create(username='admin_check', email='admin_check@example.com')
if created:
    user.set_password('password')
    user.is_staff = True
    user.save()
request.user = user

# Execute View
print("Executing Analytics View...")
try:
    response = analytics_dashboard(request)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        
        # Check for new sections and UI elements
        checks = [
            "User Retention",
            "Store Health",
            "Abandoned Carts",
            "dashboard-container", # New UI class
            "modern-table",        # New UI class
            "date-badge",          # New UI class
            "analytics-grid"       # Grid layout
        ]
        
        missing = [c for c in checks if c not in content]
        
        if not missing:
            print("SUCCESS: All new UI elements and sections found in rendered HTML.")
            
            # Verify Chart Data Presence (Looking for JSON scripts or numbers)
            if "id=\"device-data\" type=\"application/json\">" in content:
                print("SUCCESS: Device data JSON found.")
            else:
                 print("WARNING: Device data JSON missing.")
                 
            # Check for funnel numbers
            if "datasets: [{" in content and "data: [" in content:
                 print("SUCCESS: Chart datasets found.")

            # Check for Optimization (Compact Grid)
            if "md:grid-cols-2" in content:
                print("SUCCESS: Compact 2-column layout found.")
            else:
                print("WARNING: Compact layout class 'md:grid-cols-2' missing.")
        else:
            print(f"WARNING: The following UI elements were missing: {missing}")
            
    else:
        print("FAILED: View returned non-200 status.")
        
except Exception as e:
    print(f"ERROR: {e}")
