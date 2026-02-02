import requests
try:
    response = requests.get('https://albarakahmart.vercel.app/')
    print(f"Status Code: {response.status_code}")
    print(f"Content: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
