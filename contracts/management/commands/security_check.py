"""
security_check.py
=================
Custom Django management command that runs a checklist of
security settings and prints a report.

Usage:
    python manage.py security_check

Runs against the CURRENT settings (development or production,
depending on which .env is loaded). Add to your CI pipeline
to catch security regressions before deployment.
"""

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    """
    Check security settings and print a pass/fail report.
    Returns exit code 0 if all critical checks pass,
    exit code 1 if any critical check fails.
    """

    help = 'Run security settings check and print a report.'

    # ── ANSI colour helpers ────────────────────────────────
    GREEN  = '\033[92m'
    RED    = '\033[91m'
    YELLOW = '\033[93m'
    BLUE   = '\033[94m'
    RESET  = '\033[0m'
    BOLD   = '\033[1m'

    def _pass(self, message):
        self.stdout.write(f"  {self.GREEN}✅ PASS{self.RESET}  {message}")

    def _fail(self, message):
        self.stdout.write(f"  {self.RED}❌ FAIL{self.RESET}  {message}")

    def _warn(self, message):
        self.stdout.write(f"  {self.YELLOW}⚠️  WARN{self.RESET}  {message}")

    def _info(self, message):
        self.stdout.write(f"  {self.BLUE}ℹ️  INFO{self.RESET}  {message}")

    def _section(self, title):
        self.stdout.write(f"\n{self.BOLD}{title}{self.RESET}")
        self.stdout.write("─" * 60)

    # ── Main entry point ───────────────────────────────────

    def handle(self, *args, **options):
        self.stdout.write(
            f"\n{self.BOLD}"
            f"{'=' * 60}\n"
            f"  LegalTech Security Check\n"
            f"{'=' * 60}{self.RESET}\n"
        )

        failures  = []
        warnings  = []

        # ── Section 1: Core Django Security ───────────────
        self._section("1. Core Django Security")

        # SECRET_KEY must not be the dev fallback
        if settings.SECRET_KEY == 'fallback-key-replace-in-production':
            self._fail("SECRET_KEY is the insecure fallback value.")
            failures.append("SECRET_KEY not set")
        elif len(settings.SECRET_KEY) < 40:
            self._warn("SECRET_KEY is short — recommend 50+ characters.")
            warnings.append("SECRET_KEY short")
        else:
            self._pass("SECRET_KEY is set and reasonably long.")

        # DEBUG must be False in production
        if settings.DEBUG:
            self._warn(
                "DEBUG=True — acceptable in development, "
                "must be False in production."
            )
            warnings.append("DEBUG=True")
        else:
            self._pass("DEBUG=False — production-safe.")

        # ALLOWED_HOSTS must not be wildcard in production
        if not settings.DEBUG:
            if '*' in settings.ALLOWED_HOSTS:
                self._fail(
                    "ALLOWED_HOSTS contains '*' in production mode. "
                    "Set explicit hosts."
                )
                failures.append("ALLOWED_HOSTS wildcard in production")
            else:
                self._pass(
                    f"ALLOWED_HOSTS is explicit: {settings.ALLOWED_HOSTS}"
                )
        else:
            self._info(
                f"ALLOWED_HOSTS={settings.ALLOWED_HOSTS} "
                f"(DEBUG=True, so wildcard is acceptable)"
            )

        # ── Section 2: CORS ────────────────────────────────
        self._section("2. CORS Configuration")

        cors_all = getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False)
        cors_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])

        if cors_all:
            if settings.DEBUG:
                self._warn(
                    "CORS_ALLOW_ALL_ORIGINS=True is set. "
                    "Acceptable in development. "
                    "Must switch to CORS_ALLOWED_ORIGINS before production."
                )
                warnings.append("CORS_ALLOW_ALL_ORIGINS=True")
            else:
                self._fail(
                    "CORS_ALLOW_ALL_ORIGINS=True in production mode. "
                    "Set explicit CORS_ALLOWED_ORIGINS."
                )
                failures.append("CORS_ALLOW_ALL_ORIGINS=True in production")
        elif cors_origins:
            self._pass(
                f"CORS_ALLOWED_ORIGINS has {len(cors_origins)} "
                f"explicit origin(s)."
            )
            for origin in cors_origins:
                self._info(f"  Allowed origin: {origin}")
        else:
            self._warn(
                "Neither CORS_ALLOW_ALL_ORIGINS nor "
                "CORS_ALLOWED_ORIGINS is set. "
                "Dashboard integration will fail."
            )
            warnings.append("No CORS origins configured")

        # ── Section 3: Security Headers ────────────────────
        self._section("3. Security Headers")

        if getattr(settings, 'SECURE_BROWSER_XSS_FILTER', False):
            self._pass("SECURE_BROWSER_XSS_FILTER=True")
        else:
            self._warn("SECURE_BROWSER_XSS_FILTER not set.")
            warnings.append("SECURE_BROWSER_XSS_FILTER missing")

        if getattr(settings, 'X_FRAME_OPTIONS', '') == 'DENY':
            self._pass("X_FRAME_OPTIONS=DENY (clickjacking protection)")
        else:
            self._warn(
                f"X_FRAME_OPTIONS={getattr(settings, 'X_FRAME_OPTIONS', 'not set')} "
                f"— recommend DENY."
            )
            warnings.append("X_FRAME_OPTIONS not DENY")

        if getattr(settings, 'SECURE_CONTENT_TYPE_NOSNIFF', False):
            self._pass("SECURE_CONTENT_TYPE_NOSNIFF=True")
        else:
            self._warn("SECURE_CONTENT_TYPE_NOSNIFF not set.")
            warnings.append("SECURE_CONTENT_TYPE_NOSNIFF missing")

        # HTTPS settings only required in production
        if not settings.DEBUG:
            if getattr(settings, 'SECURE_SSL_REDIRECT', False):
                self._pass("SECURE_SSL_REDIRECT=True (production)")
            else:
                self._fail(
                    "SECURE_SSL_REDIRECT=False in production mode. "
                    "Enable HTTPS redirect."
                )
                failures.append("SECURE_SSL_REDIRECT=False in production")

            if getattr(settings, 'SESSION_COOKIE_SECURE', False):
                self._pass("SESSION_COOKIE_SECURE=True (production)")
            else:
                self._fail(
                    "SESSION_COOKIE_SECURE=False in production. "
                    "Sessions can travel over HTTP."
                )
                failures.append("SESSION_COOKIE_SECURE=False in production")

            if getattr(settings, 'CSRF_COOKIE_SECURE', False):
                self._pass("CSRF_COOKIE_SECURE=True (production)")
            else:
                self._fail(
                    "CSRF_COOKIE_SECURE=False in production."
                )
                failures.append("CSRF_COOKIE_SECURE=False in production")
        else:
            self._info(
                "HTTPS settings (SSL redirect, secure cookies) "
                "skipped — DEBUG=True."
            )

        # ── Section 4: Database ────────────────────────────
        self._section("4. Database Configuration")

        db_cfg = settings.DATABASES.get('default', {})

        if db_cfg.get('ENGINE') == 'django.db.backends.postgresql':
            self._pass("Using PostgreSQL (not SQLite).")
        else:
            self._warn(
                f"Database engine: {db_cfg.get('ENGINE')} "
                f"— recommend PostgreSQL for production."
            )
            warnings.append("Not using PostgreSQL")

        db_password = db_cfg.get('PASSWORD', '')
        if not db_password:
            self._fail("DB_PASSWORD is empty.")
            failures.append("DB_PASSWORD empty")
        elif db_password in ('postgres', 'password', '123456', 'admin'):
            self._warn(
                f"DB_PASSWORD '{db_password}' is a common weak password. "
                f"Change before production."
            )
            warnings.append("Weak DB_PASSWORD")
        else:
            self._pass("DB_PASSWORD is set (non-empty, non-default).")

        conn_max = db_cfg.get('CONN_MAX_AGE', 0)
        if conn_max > 0:
            self._pass(
                f"CONN_MAX_AGE={conn_max}s "
                f"(connection pooling enabled)."
            )
        else:
            self._warn(
                "CONN_MAX_AGE=0 — a new DB connection is opened "
                "for every request. Consider setting to 60."
            )
            warnings.append("CONN_MAX_AGE=0")

        # ── Section 5: File Uploads ─────────────────────────
        self._section("5. File Upload Limits")

        max_upload = getattr(
            settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 0
        )
        max_data   = getattr(
            settings, 'DATA_UPLOAD_MAX_MEMORY_SIZE', 0
        )
        limit_mb   = 10 * 1024 * 1024

        if max_upload <= limit_mb:
            self._pass(
                f"FILE_UPLOAD_MAX_MEMORY_SIZE="
                f"{max_upload // (1024*1024)}MB (≤ 10MB)."
            )
        else:
            self._warn(
                f"FILE_UPLOAD_MAX_MEMORY_SIZE="
                f"{max_upload // (1024*1024)}MB — above 10MB limit."
            )
            warnings.append("FILE_UPLOAD_MAX_MEMORY_SIZE > 10MB")

        if max_data <= limit_mb:
            self._pass(
                f"DATA_UPLOAD_MAX_MEMORY_SIZE="
                f"{max_data // (1024*1024)}MB (≤ 10MB)."
            )
        else:
            self._warn(
                f"DATA_UPLOAD_MAX_MEMORY_SIZE="
                f"{max_data // (1024*1024)}MB — above 10MB."
            )
            warnings.append("DATA_UPLOAD_MAX_MEMORY_SIZE > 10MB")

        # ── Summary ────────────────────────────────────────
        self._section("Summary")

        self.stdout.write(
            f"\n  Failures : {self.RED}{len(failures)}{self.RESET}"
        )
        self.stdout.write(
            f"  Warnings : {self.YELLOW}{len(warnings)}{self.RESET}"
        )

        if failures:
            self.stdout.write(
                f"\n{self.RED}CRITICAL ISSUES FOUND:{self.RESET}"
            )
            for f in failures:
                self.stdout.write(f"  • {f}")
            self.stdout.write("")
            raise SystemExit(1)
        elif warnings:
            self.stdout.write(
                f"\n{self.YELLOW}Warnings exist but no critical failures."
                f"\nSafe for development — review before production."
                f"{self.RESET}\n"
            )
        else:
            self.stdout.write(
                f"\n{self.GREEN}All security checks passed!{self.RESET}\n"
            )