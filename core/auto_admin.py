import os
import logging
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

def ensure_superuser_synced():
    """
    Safely creates or updates the administrative superuser from environment variables.
    Executed on WSGI server startup and in management commands to guarantee that changes to
    ADMIN_USERNAME, ADMIN_EMAIL, or ADMIN_PASSWORD on Render take effect immediately upon container start.
    """
    try:
        User = get_user_model()
        username = os.getenv('ADMIN_USERNAME', 'admin').strip()
        email = os.getenv('ADMIN_EMAIL', 'admin@pawanmod.com').strip()
        password = os.getenv('ADMIN_PASSWORD', 'admin123').strip()

        if not username or not password:
            return

        superuser = User.objects.filter(is_superuser=True).first() or User.objects.filter(username__iexact=username).first()

        if superuser:
            updated = False
            if superuser.username != username:
                superuser.username = username
                updated = True
            if superuser.email != email:
                superuser.email = email
                updated = True
            if not superuser.check_password(password):
                superuser.set_password(password)
                updated = True
            if not superuser.is_superuser:
                superuser.is_superuser = True
                updated = True
            if not superuser.is_staff:
                superuser.is_staff = True
                updated = True
            if not superuser.is_active:
                superuser.is_active = True
                updated = True
            
            if updated:
                superuser.save()
                logger.info(f"Superuser '{username}' credentials synchronized successfully.")
        else:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            logger.info(f"Superuser '{username}' created successfully.")
    except Exception as e:
        # Defer if database tables are not migrated yet
        logger.warning(f"Superuser auto-sync deferred: {e}")
