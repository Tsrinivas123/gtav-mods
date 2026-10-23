import sys
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError

class Command(BaseCommand):
    help = 'Safely verifies database connectivity without exposing secrets or passwords.'

    def handle(self, *args, **options):
        db_settings = connection.settings_dict
        engine = db_settings.get('ENGINE', '')
        host = db_settings.get('HOST', '')
        name = db_settings.get('NAME', '')
        port = db_settings.get('PORT', '')

        self.stdout.write(self.style.MIGRATE_HEADING("=== PawanMod Database Connectivity Check ==="))
        self.stdout.write(f"Database Engine: {engine}")
        self.stdout.write(f"Database Name:   {name}")
        self.stdout.write(f"Database Host:   {host or '(default/socket)'}")
        self.stdout.write(f"Database Port:   {port or '(default)'}")

        if host and host.startswith('dpg-') and '.' not in host:
            self.stdout.write(self.style.WARNING(
                "\n[WARNING] Render Internal Hostname Detected!\n"
                f"Host '{host}' is an internal Render private network address.\n"
                "It cannot be resolved outside Render (such as on Vercel or local machine).\n"
                "Please replace DATABASE_URL with the 'External Database URL' from your Render PostgreSQL dashboard."
            ))

        self.stdout.write("\nAttempting connection to database...")
        try:
            connection.ensure_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                result = cursor.fetchone()
            if result and result[0] == 1:
                self.stdout.write(self.style.SUCCESS("[PASS] Database connection verified successfully!"))
                return
        except OperationalError as err:
            self.stdout.write(self.style.ERROR(f"[FAIL] OperationalError: {err}"))
            if 'could not translate host name' in str(err):
                self.stdout.write(self.style.WARNING(
                    "\nRoot Cause: Hostname could not be translated by DNS.\n"
                    "The hostname does not exist in public DNS.\n"
                    "Action Required: Copy the 'External Database URL' from Render Dashboard -> PostgreSQL -> Connect."
                ))
            sys.exit(1)
        except Exception as err:
            self.stdout.write(self.style.ERROR(f"[FAIL] Unexpected database error: {type(err).__name__}: {err}"))
            sys.exit(1)
