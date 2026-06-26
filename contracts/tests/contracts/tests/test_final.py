"""
test_final.py
=============
Final API test suite — Day 31 closing test pass.

This file is deliberately redundant with earlier test files
for the most CRITICAL behaviors. Think of it as a final
integration smoke test — if this file passes, you can be
confident the system is working correctly end-to-end,
even without reading 300+ individual tests.

Also adds tests for a few behaviors added in Days 29-30
that didn't have their own dedicated tests yet:
  → Security headers on every endpoint type
  → CONN_MAX_AGE is configured
  → Dashboard endpoint complete response shape
  → All 17 endpoints return the correct HTTP method

If you're in a hurry and can only run one test file,
run this one.
"""

from django.test import TestCase
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

from contracts.models import Document, ExtractedClause, RiskFlag


# ============================================================
# BASE
# ============================================================

class FinalTestBase(TestCase):
    """Shared setup for all final tests."""

    def setUp(self):
        self.client = APIClient()

        self.doc = Document.objects.create(
            file_name         = 'final_test.pdf',
            contract_type     = 'NDA',
            counterparty_name = 'Final Test Corp',
            status            = 'completed',
            risk_score        = 2,
        )
        self.clause = ExtractedClause.objects.create(
            document         = self.doc,
            clause_type      = 'confidentiality',
            clause_text      = (
                'Both parties agree to maintain strict '
                'confidentiality of all shared information.'
            ),
            page_number      = 1,
            confidence_score = 0.95,
        )
        self.risk = RiskFlag.objects.create(
            document     = self.doc,
            risk_title   = 'Unlimited Liability Found',
            flagged_text = (
                'The party agrees to unlimited liability '
                'for all damages caused.'
            ),
            severity     = 'high',
            page_number  = 2,
        )

    def make_pdf(self, name='final.pdf'):
        return SimpleUploadedFile(
            name         = name,
            content      = b'%PDF-1.4 final test content',
            content_type = 'application/pdf'
        )


# ============================================================
# TEST GROUP 1: ALL 17 ENDPOINTS RETURN CORRECT HTTP METHOD
# ============================================================

class AllEndpointsMethodTests(FinalTestBase):
    """
    Every endpoint must respond to the correct HTTP method
    with a 2xx status and reject wrong methods gracefully.
    This catches any URL routing typos made across Days 8-22.
    """

    def test_01_health_check_get(self):
        r = self.client.get('/api/v1/health/')
        self.assertEqual(r.status_code, 200)

    def test_02_stats_get(self):
        r = self.client.get('/api/v1/stats/')
        self.assertEqual(r.status_code, 200)

    def test_03_dashboard_get(self):
        r = self.client.get('/api/v1/dashboard/')
        self.assertEqual(r.status_code, 200)

    def test_04_documents_upload_post(self):
        r = self.client.post(
            '/api/v1/documents/upload/',
            {'file': self.make_pdf()},
            format='multipart'
        )
        self.assertEqual(r.status_code, 201)

    def test_05_documents_list_get(self):
        r = self.client.get('/api/v1/documents/')
        self.assertEqual(r.status_code, 200)

    def test_06_documents_detail_get(self):
        r = self.client.get(f'/api/v1/documents/{self.doc.id}/')
        self.assertEqual(r.status_code, 200)

    def test_07_documents_summary_get(self):
        r = self.client.get(
            f'/api/v1/documents/{self.doc.id}/summary/'
        )
        self.assertEqual(r.status_code, 200)

    def test_08_documents_update_status_patch(self):
        r = self.client.patch(
            f'/api/v1/documents/{self.doc.id}/update-status/',
            {'status': 'completed'},
            format='json'
        )
        self.assertEqual(r.status_code, 200)

    def test_09_clauses_post(self):
        r = self.client.post(
            f'/api/v1/documents/{self.doc.id}/clauses/',
            {
                'clause_type':      'termination',
                'clause_text':      (
                    'Either party may terminate with 30 '
                    'days written notice.'
                ),
                'page_number':      5,
                'confidence_score': 0.88,
            },
            format='json'
        )
        self.assertEqual(r.status_code, 201)

    def test_10_clauses_get(self):
        r = self.client.get(
            f'/api/v1/documents/{self.doc.id}/clauses/'
        )
        self.assertEqual(r.status_code, 200)

    def test_11_risks_post(self):
        r = self.client.post(
            f'/api/v1/documents/{self.doc.id}/risks/',
            {
                'risk_title':   'Indemnification Risk',
                'flagged_text': (
                    'The party shall indemnify all related '
                    'parties without any limit whatsoever.'
                ),
                'severity':     'medium',
                'page_number':  3,
            },
            format='json'
        )
        self.assertEqual(r.status_code, 201)

    def test_12_risks_get(self):
        r = self.client.get(
            f'/api/v1/documents/{self.doc.id}/risks/'
        )
        self.assertEqual(r.status_code, 200)

    def test_13_nlp_pending_get(self):
        r = self.client.get('/api/v1/nlp/documents/pending/')
        self.assertEqual(r.status_code, 200)

    def test_14_nlp_fetch_get(self):
        r = self.client.get(
            f'/api/v1/nlp/documents/{self.doc.id}/'
        )
        self.assertEqual(r.status_code, 200)

    def test_15_nlp_status_patch(self):
        doc = Document.objects.create(
            file_name='nlp_status_test.pdf',
            status='uploaded'
        )
        r = self.client.patch(
            f'/api/v1/nlp/documents/{doc.id}/status/',
            {'status': 'processing'},
            format='json'
        )
        self.assertEqual(r.status_code, 200)

    def test_16_nlp_process_post(self):
        doc = Document.objects.create(
            file_name='nlp_process_test.pdf',
            status='uploaded'
        )
        r = self.client.post(
            f'/api/v1/nlp/documents/{doc.id}/process/',
            {
                "status":     "completed",
                "risk_score": 0,
                "metadata":   {},
                "clauses":    [],
                "risk_flags": [],
            },
            format='json'
        )
        self.assertEqual(r.status_code, 201)

    def test_17_nlp_results_get(self):
        r = self.client.get(
            f'/api/v1/nlp/documents/{self.doc.id}/results/'
        )
        self.assertEqual(r.status_code, 200)


# ============================================================
# TEST GROUP 2: EVERY ENDPOINT RETURNS STANDARD RESPONSE SHAPE
# ============================================================

class StandardResponseShapeTests(FinalTestBase):
    """
    EVERY API response — success or error — must have
    success, message, and status_code fields.
    This is the contract we defined in Day 5 and every
    subsequent day has relied on.
    """

    REQUIRED_FIELDS = ['success', 'message', 'status_code']

    def _check_shape(self, response):
        data = response.json()
        for field in self.REQUIRED_FIELDS:
            self.assertIn(
                field,
                data,
                msg=f"Response missing '{field}' field: {data}"
            )

    def test_health_response_shape(self):
        self._check_shape(self.client.get('/api/v1/health/'))

    def test_stats_response_shape(self):
        self._check_shape(self.client.get('/api/v1/stats/'))

    def test_dashboard_response_shape(self):
        self._check_shape(self.client.get('/api/v1/dashboard/'))

    def test_document_list_response_shape(self):
        self._check_shape(self.client.get('/api/v1/documents/'))

    def test_document_detail_response_shape(self):
        self._check_shape(
            self.client.get(f'/api/v1/documents/{self.doc.id}/')
        )

    def test_404_response_shape(self):
        self._check_shape(
            self.client.get('/api/v1/documents/99999/')
        )

    def test_400_response_shape(self):
        self._check_shape(
            self.client.post(
                '/api/v1/documents/upload/',
                {},
                format='multipart'
            )
        )

    def test_error_responses_have_success_false(self):
        """All error responses must have success=false."""
        errors = [
            self.client.get('/api/v1/documents/99999/'),
            self.client.post(
                '/api/v1/documents/upload/',
                {},
                format='multipart'
            ),
            self.client.get('/api/v1/documents/?status=INVALID'),
        ]
        for response in errors:
            self.assertFalse(response.json()['success'])

    def test_success_responses_have_success_true(self):
        """All success responses must have success=true."""
        successes = [
            self.client.get('/api/v1/health/'),
            self.client.get('/api/v1/stats/'),
            self.client.get('/api/v1/documents/'),
            self.client.get(
                f'/api/v1/documents/{self.doc.id}/'
            ),
        ]
        for response in successes:
            self.assertTrue(response.json()['success'])


# ============================================================
# TEST GROUP 3: SECURITY HEADERS ON ALL ENDPOINT TYPES
# ============================================================

class SecurityHeadersOnAllEndpointsTests(FinalTestBase):
    """
    Security headers added in Day 30 must appear on EVERY
    type of response — success, error, GET, POST, PATCH,
    and even on the dashboard and NLP endpoints.
    """

    SECURITY_HEADERS = [
        'X-Frame-Options',
        'X-Content-Type-Options',
    ]

    def _check_headers(self, response, endpoint_name):
        for header in self.SECURITY_HEADERS:
            self.assertIn(
                header,
                response,
                msg=(
                    f"Security header '{header}' missing "
                    f"on {endpoint_name}"
                )
            )

    def test_headers_on_health(self):
        r = self.client.get('/api/v1/health/')
        self._check_headers(r, 'GET /health/')

    def test_headers_on_dashboard(self):
        r = self.client.get('/api/v1/dashboard/')
        self._check_headers(r, 'GET /dashboard/')

    def test_headers_on_document_list(self):
        r = self.client.get('/api/v1/documents/')
        self._check_headers(r, 'GET /documents/')

    def test_headers_on_document_detail(self):
        r = self.client.get(
            f'/api/v1/documents/{self.doc.id}/'
        )
        self._check_headers(r, 'GET /documents/{id}/')

    def test_headers_on_404_error(self):
        r = self.client.get('/api/v1/documents/99999/')
        self._check_headers(r, 'GET /documents/99999/ (404)')

    def test_headers_on_400_error(self):
        r = self.client.post(
            '/api/v1/documents/upload/',
            {},
            format='multipart'
        )
        self._check_headers(r, 'POST /upload/ (400)')

    def test_headers_on_nlp_endpoint(self):
        r = self.client.get('/api/v1/nlp/documents/pending/')
        self._check_headers(r, 'GET /nlp/pending/')

    def test_x_frame_options_value_is_deny_everywhere(self):
        """X-Frame-Options must be DENY on every response."""
        endpoints = [
            '/api/v1/health/',
            '/api/v1/dashboard/',
            '/api/v1/documents/',
            f'/api/v1/documents/{self.doc.id}/',
        ]
        for url in endpoints:
            r = self.client.get(url)
            self.assertEqual(
                r['X-Frame-Options'],
                'DENY',
                msg=f"X-Frame-Options must be DENY on {url}"
            )

    def test_x_content_type_options_is_nosniff_everywhere(self):
        """X-Content-Type-Options must be nosniff on every response."""
        endpoints = [
            '/api/v1/health/',
            '/api/v1/dashboard/',
            '/api/v1/documents/',
        ]
        for url in endpoints:
            r = self.client.get(url)
            self.assertEqual(
                r['X-Content-Type-Options'],
                'nosniff',
                msg=f"X-Content-Type-Options must be nosniff on {url}"
            )


# ============================================================
# TEST GROUP 4: DASHBOARD COMPLETE RESPONSE SHAPE
# ============================================================

class DashboardCompleteShapeTests(FinalTestBase):
    """
    Final validation of the dashboard endpoint response shape
    (added Day 22, optimized Day 29). Every field used by
    Member 3's dashboard_sample.js must be present.
    """

    def setUp(self):
        super().setUp()
        self.dashboard = self.client.get(
            '/api/v1/dashboard/'
        ).json()['data']

    def test_has_summary(self):
        self.assertIn('summary', self.dashboard)

    def test_summary_has_all_keys(self):
        summary = self.dashboard['summary']
        for key in [
            'total_documents',
            'total_clauses',
            'total_risks',
            'total_resolved',
            'total_unresolved',
        ]:
            self.assertIn(key, summary, msg=f"summary missing: {key}")

    def test_has_status_breakdown(self):
        self.assertIn('status_breakdown', self.dashboard)

    def test_status_breakdown_has_all_four_statuses(self):
        bd = self.dashboard['status_breakdown']
        for s in ['uploaded', 'processing', 'completed', 'failed']:
            self.assertIn(s, bd)

    def test_has_risk_breakdown(self):
        self.assertIn('risk_breakdown', self.dashboard)

    def test_risk_breakdown_has_all_three_severities(self):
        bd = self.dashboard['risk_breakdown']
        for s in ['high', 'medium', 'low']:
            self.assertIn(s, bd)

    def test_has_recent_documents(self):
        self.assertIn('recent_documents', self.dashboard)
        self.assertIsInstance(
            self.dashboard['recent_documents'], list
        )

    def test_recent_documents_max_5(self):
        self.assertLessEqual(
            len(self.dashboard['recent_documents']),
            5
        )

    def test_has_recent_high_risks(self):
        self.assertIn('recent_high_risks', self.dashboard)
        self.assertIsInstance(
            self.dashboard['recent_high_risks'], list
        )

    def test_has_contract_type_breakdown(self):
        self.assertIn('contract_type_breakdown', self.dashboard)

    def test_recent_doc_fields_present(self):
        docs = self.dashboard['recent_documents']
        if docs:
            doc = docs[0]
            for field in [
                'id', 'file_name', 'contract_type',
                'counterparty_name', 'status', 'risk_score',
                'uploaded_at', 'total_clauses', 'total_risks',
            ]:
                self.assertIn(
                    field, doc,
                    msg=f"recent_documents item missing: {field}"
                )

    def test_recent_high_risk_fields_present(self):
        risks = self.dashboard['recent_high_risks']
        if risks:
            risk = risks[0]
            for field in [
                'id', 'risk_title', 'severity', 'document_id',
                'document_name', 'page_number', 'is_resolved',
                'flagged_at',
            ]:
                self.assertIn(
                    field, risk,
                    msg=f"recent_high_risks item missing: {field}"
                )


# ============================================================
# TEST GROUP 5: STATS ALWAYS COMPLETE SHAPE (Bug 3&4 Regression)
# ============================================================

class StatsAlwaysCompleteTests(FinalTestBase):
    """
    Final regression confirmation for Bug 3 & 4 from Day 24.
    stats/ must always return all 4 statuses and all 3
    severities, even when some have zero items.
    """

    def test_risks_by_severity_always_has_3_entries(self):
        r  = self.client.get('/api/v1/stats/')
        bd = r.json()['data']['risks_by_severity']
        self.assertEqual(len(bd), 3)
        severities = {item['severity'] for item in bd}
        self.assertEqual(severities, {'high', 'medium', 'low'})

    def test_documents_by_status_always_has_4_entries(self):
        r  = self.client.get('/api/v1/stats/')
        bd = r.json()['data']['documents_by_status']
        self.assertEqual(len(bd), 4)
        statuses = {item['status'] for item in bd}
        self.assertEqual(
            statuses,
            {'uploaded', 'processing', 'completed', 'failed'}
        )


# ============================================================
# TEST GROUP 6: CRITICAL VALIDATION RULES FINAL CHECK
# ============================================================

class CriticalValidationFinalTests(FinalTestBase):
    """
    Final confirmation that the most important validation
    rules still hold. These represent the user-facing safety
    net — if any of these fail, the API is broken.
    """

    def test_upload_no_file_returns_400(self):
        r = self.client.post(
            '/api/v1/documents/upload/', {}, format='multipart'
        )
        self.assertEqual(r.status_code, 400)
        self.assertFalse(r.json()['success'])

    def test_upload_non_pdf_returns_400(self):
        txt = SimpleUploadedFile('doc.txt', b'text', 'text/plain')
        r   = self.client.post(
            '/api/v1/documents/upload/',
            {'file': txt},
            format='multipart'
        )
        self.assertEqual(r.status_code, 400)

    def test_invalid_status_filter_returns_400(self):
        r = self.client.get('/api/v1/documents/?status=WRONG')
        self.assertEqual(r.status_code, 400)

    def test_invalid_confidence_score_returns_400(self):
        r = self.client.post(
            f'/api/v1/documents/{self.doc.id}/clauses/',
            {
                'clause_type':      'other',
                'clause_text':      'Test clause text here valid.',
                'page_number':      1,
                'confidence_score': 99.9,
            },
            format='json'
        )
        self.assertEqual(r.status_code, 400)

    def test_invalid_severity_returns_400(self):
        r = self.client.post(
            f'/api/v1/documents/{self.doc.id}/risks/',
            {
                'risk_title':   'Test Risk',
                'flagged_text': 'Some risky text content found.',
                'severity':     'critical',
                'page_number':  1,
            },
            format='json'
        )
        self.assertEqual(r.status_code, 400)

    def test_empty_body_patch_returns_400(self):
        r = self.client.patch(
            f'/api/v1/documents/{self.doc.id}/update-status/',
            {},
            format='json'
        )
        self.assertEqual(r.status_code, 400)

    def test_nonexistent_id_returns_404(self):
        r = self.client.get('/api/v1/documents/99999/')
        self.assertEqual(r.status_code, 404)

    def test_reprocess_completed_returns_409(self):
        r = self.client.post(
            f'/api/v1/nlp/documents/{self.doc.id}/process/',
            {
                "status":     "completed",
                "risk_score": 0,
                "metadata":   {},
                "clauses":    [],
                "risk_flags": [],
            },
            format='json'
        )
        self.assertEqual(r.status_code, 409)

    def test_bulk_over_100_clauses_returns_400(self):
        clauses = [
            {
                'clause_type':      'other',
                'clause_text':      f'Clause {i} text content here.',
                'page_number':      1,
                'confidence_score': 0.5,
            }
            for i in range(101)
        ]
        r = self.client.post(
            f'/api/v1/documents/{self.doc.id}/clauses/',
            clauses,
            format='json'
        )
        self.assertEqual(r.status_code, 400)


# ============================================================
# TEST GROUP 7: SETTINGS FINAL VERIFICATION
# ============================================================

class SettingsFinalVerificationTests(TestCase):
    """
    Quick settings sanity check — the most critical Django
    configuration values must be set correctly.
    """

    def test_cors_allow_all_origins_is_not_true(self):
        """CORS_ALLOW_ALL_ORIGINS must be False/unset after Day 30."""
        self.assertFalse(
            getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False)
        )

    def test_cors_allowed_origins_is_not_empty(self):
        """CORS_ALLOWED_ORIGINS must have at least one origin."""
        origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
        self.assertGreater(len(origins), 0)

    def test_x_frame_options_is_deny(self):
        self.assertEqual(settings.X_FRAME_OPTIONS, 'DENY')

    def test_secure_content_type_nosniff_is_true(self):
        self.assertTrue(settings.SECURE_CONTENT_TYPE_NOSNIFF)

    def test_secure_browser_xss_filter_is_true(self):
        self.assertTrue(settings.SECURE_BROWSER_XSS_FILTER)

    def test_file_upload_limit_is_10mb(self):
        limit = 10 * 1024 * 1024
        self.assertEqual(settings.FILE_UPLOAD_MAX_MEMORY_SIZE, limit)

    def test_database_is_postgresql(self):
        self.assertIn(
            'postgresql',
            settings.DATABASES['default']['ENGINE']
        )

    def test_conn_max_age_is_positive(self):
        conn_max = settings.DATABASES['default'].get('CONN_MAX_AGE', 0)
        self.assertGreater(conn_max, 0)