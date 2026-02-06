import datetime
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone

class UpdateOnlineStatusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            now = timezone.now()
            # Update last_seen every request
            request.user.last_seen = now
            
            # If validly logged in, ensure is_online is True
            # (unless they explicitly set themselves invisible, but for now we assume functionality is simple)
            if not request.user.is_online:
                request.user.is_online = True
                request.user.save(update_fields=['last_seen', 'is_online'])
            else:
                # Update last_seen without forcing save every time if not needed?
                # Optimization: only save if last_seen is old > 1 min
                last = request.user.last_seen
                if not last or (now - last).total_seconds() > 60:
                    request.user.save(update_fields=['last_seen'])

        response = self.get_response(request)
        return response
