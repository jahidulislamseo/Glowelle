import os
import django
import requests

# Setup Django standalone
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client

def debug_admin_order_page():
    log_file = "debug_log.txt"
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("Attempting to access Order Admin Page...\n")
        
        c = Client()
        # Login
        logged_in = c.login(username='Jahidulf1', password='admin123')
        f.write(f"Login successful: {logged_in}\n")
        
        if not logged_in:
            f.write("Failed to login! Password might be wrong.\n")
            return

        # Access Order 2 Change View
        url = '/admin/admin/orders/order/2/change/'
        try:
            response = c.get(url)
            f.write(f"Response Status Code: {response.status_code}\n")
            
            if response.status_code == 200:
                f.write("Success! Page loaded.\n")
            else:
                f.write(f"Error! Status Code: {response.status_code}\n")
                f.write(f"Response Content:\n{response.content.decode('utf-8')}\n")
        except Exception as e:
            f.write(f"EXCEPTION: {str(e)}\n")

if __name__ == '__main__':
    debug_admin_order_page()

