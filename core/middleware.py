import logging
from django.contrib.sessions.middleware import SessionMiddleware

logger = logging.getLogger(__name__)

class SafeSessionMiddleware(SessionMiddleware):
    """
    Subclasses Django's SessionMiddleware to safely handle external database
    disconnections during response processing.
    
    If the database is unreachable or connection drops during session saving,
    logs a warning rather than crashing the entire response with HTTP 500.
    """
    def process_response(self, request, response):
        try:
            return super().process_response(request, response)
        except Exception as exc:
            logger.warning("SafeSessionMiddleware: Could not save session to database: %s", exc)
            return response
