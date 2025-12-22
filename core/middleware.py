from django.core.cache import cache
import time

class ActiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith('/static/') and not request.path.startswith('/media/'):
            self.track_user(request)
        
        response = self.get_response(request)
        return response

    def track_user(self, request):
        # 1. Identify User
        if request.user.is_authenticated:
            ident = f"user_{request.user.id}"
        else:
            # Ensure session exists
            if not request.session.session_key:
                request.session.save()
            ident = f"guest_{request.session.session_key}"

        # 2. Load Stats
        online_users = cache.get('online_users', {})
        
        # 3. Update Current
        current_ts = time.time()
        online_users[ident] = current_ts
        
        # 4. Prune Old (> 5 mins / 300s)
        valid_users = {k: v for k, v in online_users.items() if (current_ts - v) < 300}
        
        # 5. Save back
        cache.set('online_users', valid_users, 3600)  # TTL 1 hour (rolling)
