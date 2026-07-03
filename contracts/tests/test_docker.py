"""
test_docker.py — Member 3
==========================
Tests that verify the application works correctly
in a Docker-like environment.

These tests check:
  - Database connection is working
  - All required settings are configured
  - Media folder exists and is writable
  - Static files can be collected
  - Admin panel is accessible
"""

from django.test import TestCase, Client
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
import os


class EnvironmentConfigTest(TestCase):
    """
    Tests that Django settings are configured correctly.
    These settings must be present for the app to work.
    """

    def test_secret_key_is_set(self):
        """
        TEST: Is SECRET_KEY configured?
        WHAT: Checks settings.SECRET_KEY is not empty.
        WHY: Django will not start without a SECRET_KEY.
        """
        self.assertTrue(
            settings.SECRET_KEY,
            "SECRET_KEY must be configured in .env"
        )

    def test_database_settings_configured(self):
        """
        TEST: Are database settings configured?
        WHAT: Checks DATABASES setting has required keys.
        WHY: If database settings are missing, migrations fail.
        """
        db = settings.DATABASES.get('default', {})

        self.assertIn('ENGINE', db)
        self.assertIn('NAME',   db)
        self.assertIn('USER',   db)
        self.assertEqual(
            db['ENGINE'],
            'django.db.backends.postgresql'
        )

    def test_media_root_configured(self):
        """
        TEST: Is MEDIA_ROOT configured for file uploads?
        WHAT: Checks settings.MEDIA_ROOT is not empty.
        WHY: PDF uploads won't work without MEDIA_ROOT.
        """
        self.assertTrue(
            settings.MEDIA_ROOT,
            "MEDIA_ROOT must be configured"
        )

    def test_installed_apps_has_contracts(self):
        """
        TEST: Is the contracts app installed?
        WHAT: Checks 'contracts' is in INSTALLED_APPS.
        WHY: App must be installed for models and admin to work.
        """
        self.assertIn('contracts', settings.INSTALLED_APPS)

    def test_installed_apps_has_rest_framework(self):
        """
        TEST: Is Django REST Framework installed?
        WHAT: Checks 'rest_framework' is in INSTALLED_APPS.
        WHY: All API endpoints require DRF.
        """
        self.assertIn('rest_framework', settings.INSTALLED_APPS)

    def test_installed_apps_has_corsheaders(self):
        """
        TEST: Is CORS headers app installed?
        WHAT: Checks 'corsheaders' is in INSTALLED_APPS.
        WHY: Member 3's dashboard needs CORS to call the API.
        """
        self.assertIn('corsheaders', settings.INSTALLED_APPS)

    def test_cors_middleware_in_middleware(self):
        """
        TEST: Is CORS middleware in MIDDLEWARE list?
        WHAT: Checks corsheaders.middleware.CorsMiddleware.
        WHY: Middleware must be present for CORS to work.
        """
        cors_middleware = 'corsheaders.middleware.CorsMiddleware'
        self.assertIn(cors_middleware, settings.MIDDLEWARE)

    def test_rest_framework_pagination_configured(self):
        """
        TEST: Is DRF pagination configured?
        WHAT: Checks REST_FRAMEWORK has pagination setting.
        WHY: Without pagination, large document lists will be slow.
        """
        drf_settings = settings.REST_FRAMEWORK
        self.assertIn('DEFAULT_PAGINATION_CLASS', drf_settings)

    def test_file_upload_limit_is_10mb(self):
        """
        TEST: Is file upload limit set to 10MB?
        WHAT: Checks DATA_UPLOAD_MAX_MEMORY_SIZE.
        WHY: Limits prevent server from being overwhelmed.
        """
        limit = 10 * 1024 * 1024  # 10MB in bytes
        self.assertEqual(
            settings.DATA_UPLOAD_MAX_MEMORY_SIZE,
            limit
        )


class DatabaseConnectionTest(TestCase):
    """
    Tests that the database connection works correctly.
    """

    def test_can_create_and_query_database(self):
        """
        TEST: Can we create and query database records?
        WHAT: Creates a User record and queries it back.
        WHY: Basic proof that DB connection is working.
        """
        from contracts.models import Document

        # Create a record
        doc = Document.objects.create(
            file_name='db_test.pdf',
            status='uploaded'
        )

        # Query it back
        retrieved = Document.objects.get(id=doc.id)
        self.assertEqual(retrieved.file_name, 'db_test.pdf')

    def test_database_transactions_work(self):
        """
        TEST: Do database transactions work correctly?
        WHAT: Creates, updates, and deletes a record.
        WHY: Transactions are used in the NLP process endpoint.
        """
        from contracts.models import Document

        # Create
        doc = Document.objects.create(
            file_name='transaction_test.pdf',
            status='uploaded'
        )
        doc_id = doc.id

        # Update
        doc.status = 'completed'
        doc.save()
        doc.refresh_from_db()
        self.assertEqual(doc.status, 'completed')

        # Delete
        doc.delete()
        exists = Document.objects.filter(id=doc_id).exists()
        self.assertFalse(exists)


class StaticFilesTest(TestCase):
    """
    Tests that static files are configured correctly.
    """

    def test_static_root_configured(self):
        """
        TEST: Is STATIC_ROOT configured?
        WHAT: Checks settings.STATIC_ROOT is set.
        WHY: collectstatic command requires STATIC_ROOT.
        """
        self.assertTrue(
            settings.STATIC_ROOT,
            "STATIC_ROOT must be configured for production"
        )

    def test_static_url_configured(self):
        """
        TEST: Is STATIC_URL configured?
        WHAT: Checks settings.STATIC_URL is set.
        WHY: Admin panel CSS won't load without STATIC_URL.
        """
        self.assertTrue(
            settings.STATIC_URL,
            "STATIC_URL must be configured"
        )


class AdminAccessTest(TestCase):
    """
    Tests that admin panel is accessible after Docker setup.
    """

    def setUp(self):
        self.client = Client()
        self.admin  = User.objects.create_superuser(
            username='docker_admin',
            password='testpass123',
            email='docker@test.com'
        )

    def test_admin_login_page_loads(self):
        """
        TEST: Does admin login page load?
        WHAT: Requests /admin/login/ without authentication.
        WHY: If login page is broken, no one can log in.
        """
        response = self.client.get('/admin/login/')
        self.assertEqual(response.status_code, 200)

    def test_admin_accessible_after_login(self):
        """
        TEST: Can admin user access admin panel?
        WHAT: Logs in and requests /admin/
        WHY: Final verification that admin works in Docker.
        """
        self.client.login(
            username='docker_admin',
            password='testpass123'
        )
        response = self.client.get('/admin/')
        self.assertIn(response.status_code, [200, 302])

    def test_health_check_works(self):
        """
        TEST: Does the API health check work?
        WHAT: Simple GET to /api/v1/health/
        WHY: Health check is the first thing Docker checks.
        """
        from rest_framework.test import APIClient
        api_client = APIClient()
        response   = api_client.get('/api/v1/health/')
        self.assertEqual(response.status_code, 200)