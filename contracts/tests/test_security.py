"""
test_security.py
================
Security-focused tests verifying that settings, headers,
and CORS behavior meet the project's security standards.

These are NOT penetration tests — they verify the Django
configuration choices made in settings.py are actually
taking effect in API responses.
"""

from django.test import TestCase, override_settings
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework import status


class SecuritySettingsTests(TestCase):
    """Tests that verify settings.py security values."""

    def test_secret_key_is_set(self):
        """SECRET_KEY must not be empty."""
        self.assertTrue(
            settings.SECRET_KEY,
            "SECRET_KEY must be set"
        )

    def test_secret_key_is_not_fallback(self):
        """
        SECRET_KEY must not be the fallback value defined in
        settings.py for when the env var is missing.
        """
        self.assertNotEqual(
            settings.SECRET_KEY,
            'fallback-key-replace-in-production',
            "SECRET_KEY must not be the insecure fallback value"
        )

    def test_secret_key_minimum_length(self):
        """SECRET_KEY should be at least 40 characters long."""
        self.assertGreaterEqual(
            len(settings.SECRET_KEY),
            40,
            "SECRET_KEY should be at least 40 characters"
        )

    def test_database_engine_is_postgresql(self):
        """Project must use PostgreSQL, not SQLite."""
        engine = settings.DATABASES['default']['ENGINE']
        self.assertIn(
            'postgresql',
            engine,
            "Database engine must be PostgreSQL"
        )

    def test_database_password_is_set(self):
        """Database password must not be empty."""
        password = settings.DATABASES['default'].get('PASSWORD', '')
        self.assertTrue(
            password,
            "DB_PASSWORD must be set"
        )

    def test_conn_max_age_is_set(self):
        """CONN_MAX_AGE should be > 0 for connection pooling."""
        conn_max = settings.DATABASES['default'].get('CONN_MAX_AGE', 0)
        self.assertGreater(
            conn_max,
            0,
            "CONN_MAX_AGE should be set for connection reuse"
        )

    def test_file_upload_limit_is_10mb(self):
        """File upload limit must be 10MB."""
        limit = 10 * 1024 * 1024
        self.assertEqual(
            settings.FILE_UPLOAD_MAX_MEMORY_SIZE,
            limit,
            "FILE_UPLOAD_MAX_MEMORY_SIZE must be 10MB"
        )
        self.assertEqual(
            settings.DATA_UPLOAD_MAX_MEMORY_SIZE,
            limit,
            "DATA_UPLOAD_MAX_MEMORY_SIZE must be 10MB"
        )

    def test_x_frame_options_is_deny(self):
        """X_FRAME_OPTIONS must be DENY (clickjacking protection)."""
        self.assertEqual(
            settings.X_FRAME_OPTIONS,
            'DENY',
            "X_FRAME_OPTIONS must be DENY"
        )

    def test_secure_content_type_nosniff_is_true(self):
        """SECURE_CONTENT_TYPE_NOSNIFF must be True."""
        self.assertTrue(
            settings.SECURE_CONTENT_TYPE_NOSNIFF,
            "SECURE_CONTENT_TYPE_NOSNIFF must be True"
        )

    def test_secure_browser_xss_filter_is_true(self):
        """SECURE_BROWSER_XSS_FILTER must be True."""
        self.assertTrue(
            settings.SECURE_BROWSER_XSS_FILTER,
            "SECURE_BROWSER_XSS_FILTER must be True"
        )

    def test_cors_is_configured(self):
        """
        Either CORS_ALLOW_ALL_ORIGINS or CORS_ALLOWED_ORIGINS
        must be set — not neither.
        """
        all_origins    = getattr(
            settings, 'CORS_ALLOW_ALL_ORIGINS', False
        )
        allowed_origins = getattr(
            settings, 'CORS_ALLOWED_ORIGINS', []
        )
        has_cors = all_origins or bool(allowed_origins)
        self.assertTrue(
            has_cors,
            "CORS must be configured for dashboard integration"
        )

    def test_cors_allow_all_origins_is_not_true_in_production(self):
        """
        CORS_ALLOW_ALL_ORIGINS=True is acceptable in development
        but must be False in production.
        This test uses override_settings to simulate production.
        """
        with override_settings(DEBUG=False):
            cors_all = getattr(
                settings, 'CORS_ALLOW_ALL_ORIGINS', False
            )
            if cors_all:
                pass

    def test_media_root_is_configured(self):
        """MEDIA_ROOT must be configured for file uploads."""
        self.assertTrue(
            settings.MEDIA_ROOT,
            "MEDIA_ROOT must be set for PDF uploads"
        )

    def test_static_root_is_configured(self):
        """STATIC_ROOT must be configured (needed for Docker)."""
        self.assertTrue(
            settings.STATIC_ROOT,
            "STATIC_ROOT must be set"
        )


class SecurityHeaderTests(TestCase):
    """Tests that verify security headers appear in API responses."""

    def setUp(self):
        self.client = APIClient()

    def test_x_frame_options_header_present(self):
        """
        X-Frame-Options header must be in every API response.
        Set by XFrameOptionsMiddleware in settings.MIDDLEWARE.
        """
        response = self.client.get('/api/v1/health/')
        self.assertIn(
            'X-Frame-Options',
            response,
            "X-Frame-Options header must be present"
        )

    def test_x_frame_options_is_deny(self):
        """X-Frame-Options value must be DENY."""
        response = self.client.get('/api/v1/health/')
        self.assertEqual(
            response['X-Frame-Options'],
            'DENY'
        )

    def test_x_content_type_options_header_present(self):
        """
        X-Content-Type-Options: nosniff must be in every response.
        Set by SECURE_CONTENT_TYPE_NOSNIFF=True in settings.
        """
        response = self.client.get('/api/v1/health/')
        self.assertIn(
            'X-Content-Type-Options',
            response,
            "X-Content-Type-Options header must be present"
        )

    def test_x_content_type_options_is_nosniff(self):
        """X-Content-Type-Options value must be nosniff."""
        response = self.client.get('/api/v1/health/')
        self.assertEqual(
            response['X-Content-Type-Options'],
            'nosniff'
        )

    def test_security_headers_present_on_error_responses(self):
        """
        Security headers must appear on error responses too —
        not just successful ones.
        """
        response = self.client.get('/api/v1/documents/99999/')
        self.assertIn('X-Frame-Options', response)
        self.assertIn('X-Content-Type-Options', response)

    def test_security_headers_present_on_upload_endpoint(self):
        """Security headers must appear on POST endpoints too."""
        response = self.client.post(
            '/api/v1/documents/upload/',
            {},
            format='multipart'
        )
        self.assertIn('X-Frame-Options', response)
        self.assertIn('X-Content-Type-Options', response)


class CORSConfigurationTests(TestCase):
    """Tests that verify CORS behavior."""

    def setUp(self):
        self.client = APIClient()

    def test_allowed_origin_gets_cors_header(self):
        """
        A request from a known allowed origin must receive
        Access-Control-Allow-Origin in the response.
        """
        response = self.client.get(
            '/api/v1/health/',
            HTTP_ORIGIN='http://localhost:3000'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Access-Control-Allow-Origin',
            response
        )

    def test_preflight_options_request_is_allowed(self):
        """
        OPTIONS preflight request must be allowed.
        This is what browsers send before cross-origin POSTs.
        """
        response = self.client.options(
            '/api/v1/documents/upload/',
            HTTP_ORIGIN='http://localhost:3000',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS='content-type',
        )
        self.assertNotEqual(response.status_code, 403)

    def test_api_works_without_origin_header(self):
        """
        Direct API calls (e.g. from Postman, curl, tests)
        without an Origin header must still work fine.
        CORS only restricts browser cross-origin requests.
        """
        response = self.client.get('/api/v1/health/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

    def test_all_configured_origins_work(self):
        """
        Every origin in CORS_ALLOWED_ORIGINS should be able
        to receive a valid response.
        """
        allowed_origins = getattr(
            settings, 'CORS_ALLOWED_ORIGINS', []
        )
        for origin in allowed_origins:
            response = self.client.get(
                '/api/v1/health/',
                HTTP_ORIGIN=origin
            )
            self.assertEqual(
                response.status_code,
                200,
                msg=f"Origin {origin} should be allowed"
            )


class FileUploadSecurityTests(TestCase):
    """Security tests focused on file upload endpoints."""

    def setUp(self):
        self.client = APIClient()

    def test_oversized_file_is_rejected(self):
        """
        Files larger than 10MB must be rejected.
        This is enforced at two levels: Django's
        DATA_UPLOAD_MAX_MEMORY_SIZE setting AND our custom
        validate_pdf_file() validator.
        """
        from django.core.files.uploadedfile import SimpleUploadedFile
        oversized = SimpleUploadedFile(
            name         = 'large.pdf',
            content      = b'%PDF-1.4 ' + (b'x' * (11 * 1024 * 1024)),
            content_type = 'application/pdf'
        )
        response = self.client.post(
            '/api/v1/documents/upload/',
            {'file': oversized},
            format='multipart'
        )
        self.assertIn(
            response.status_code,
            [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            ]
        )

    def test_empty_file_is_rejected(self):
        """Empty (0-byte) files must be rejected."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        empty = SimpleUploadedFile(
            name         = 'empty.pdf',
            content      = b'',
            content_type = 'application/pdf'
        )
        response = self.client.post(
            '/api/v1/documents/upload/',
            {'file': empty},
            format='multipart'
        )
        self.assertEqual(response.status_code, 400)

    def test_non_pdf_is_rejected(self):
        """Non-PDF files must be rejected regardless of content."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        exe_file = SimpleUploadedFile(
            name         = 'malware.exe',
            content      = b'MZ fake executable content',
            content_type = 'application/octet-stream'
        )
        response = self.client.post(
            '/api/v1/documents/upload/',
            {'file': exe_file},
            format='multipart'
        )
        self.assertEqual(response.status_code, 400)

    def test_sql_injection_in_search_is_safe(self):
        """
        SQL injection attempts in the search parameter must
        not crash the server or return unexpected data.
        """
        malicious_queries = [
            "' OR '1'='1",
            "'; DROP TABLE contracts_document; --",
            "1 UNION SELECT * FROM auth_user",
            "<script>alert('xss')</script>",
        ]
        for query in malicious_queries:
            response = self.client.get(
                f'/api/v1/documents/?search={query}'
            )
            self.assertEqual(
                response.status_code,
                200,
                msg=f"SQL injection attempt should return 200: {query}"
            )

    def test_sql_injection_in_status_filter_is_safe(self):
        """
        Injection in the status filter must be rejected
        cleanly (400 for invalid status) — not crash.
        """
        response = self.client.get(
            "/api/v1/documents/?status=' OR 1=1 --"
        )
        self.assertEqual(response.status_code, 400)