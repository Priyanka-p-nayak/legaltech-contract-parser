import os
import io
import json
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

from .models import Document, ExtractedClause, RiskFlag


# ============================================================
# BASE TEST CLASS
# All test classes inherit from this.
# Sets up a test client and creates sample test data.
# ============================================================

class BaseTestCase(TestCase):
    """
    Base class with shared setup for all tests.
    Creates a test client and a sample document.
    """

    def setUp(self):
        """
        Runs before EVERY test method.
        Creates fresh test data each time.
        """
        # Test client (like Postman but automated)
        self.client = APIClient()

        # Create a fake PDF file for upload tests
        self.pdf_content = b'%PDF-1.4 fake pdf content for testing'
        self.pdf_file    = SimpleUploadedFile(
            name         = 'test_contract.pdf',
            content      = self.pdf_content,
            content_type = 'application/pdf'
        )

        # Create a test document directly in DB
        self.document = Document.objects.create(
            file_name         = 'test_contract.pdf',
            contract_type     = 'NDA',
            counterparty_name = 'Test Company Ltd',
            governing_law     = 'California, USA',
            status            = 'uploaded',
            risk_score        = 0,
        )

        # Create a test clause linked to document
        self.clause = ExtractedClause.objects.create(
            document         = self.document,
            clause_type      = 'confidentiality',
            clause_text      = (
                'Both parties agree to maintain '
                'strict confidentiality.'
            ),
            page_number      = 1,
            confidence_score = 0.95,
        )

        # Create a test risk flag linked to document
        self.risk = RiskFlag.objects.create(
            document        = self.document,
            risk_title      = 'Unlimited Liability Found',
            flagged_text    = (
                'The party agrees to unlimited liability.'
            ),
            keyword_matched = 'unlimited liability',
            severity        = 'high',
            page_number     = 2,
        )


# ============================================================
# TEST GROUP 1: HEALTH CHECK TESTS
# ============================================================

class HealthCheckTests(BaseTestCase):
    """Tests for GET /api/v1/health/"""

    def test_health_check_returns_200(self):
        """Health check should return 200 OK"""
        response = self.client.get('/api/v1/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health_check_returns_success_true(self):
        """Health check response should have success=true"""
        response = self.client.get('/api/v1/health/')
        data     = response.json()
        self.assertTrue(data['success'])

    def test_health_check_has_api_version(self):
        """Health check should include api_version"""
        response = self.client.get('/api/v1/health/')
        data     = response.json()
        self.assertIn('api_version', data['data'])
        self.assertEqual(data['data']['api_version'], '1.0.0')

    def test_health_check_has_document_count(self):
        """Health check should show total document count"""
        response = self.client.get('/api/v1/health/')
        data     = response.json()
        self.assertIn('total_documents', data['data'])
        self.assertEqual(data['data']['total_documents'], 1)


# ============================================================
# TEST GROUP 2: DOCUMENT LIST TESTS
# ============================================================

class DocumentListTests(BaseTestCase):
    """Tests for GET /api/v1/documents/"""

    def test_list_returns_200(self):
        """Document list should return 200"""
        response = self.client.get('/api/v1/documents/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_returns_documents(self):
        """Document list should return our test document"""
        response = self.client.get('/api/v1/documents/')
        data     = response.json()
        self.assertTrue(data['success'])
        self.assertIn('data', data)

    def test_filter_by_valid_status(self):
        """Filter by status=uploaded should work"""
        response = self.client.get('/api/v1/documents/?status=uploaded')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_invalid_status_returns_400(self):
        """Filter by invalid status should return 400"""
        response = self.client.get('/api/v1/documents/?status=INVALID_STATUS')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_by_filename(self):
        """Search by filename should work"""
        response = self.client.get('/api/v1/documents/?search=test_contract')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_by_counterparty(self):
        """Search by counterparty name should work"""
        response = self.client.get('/api/v1/documents/?search=Test+Company')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_pagination_page_size(self):
        """Pagination with page_size should work"""
        response = self.client.get('/api/v1/documents/?page=1&page_size=5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ============================================================
# TEST GROUP 3: DOCUMENT DETAIL TESTS
# ============================================================

class DocumentDetailTests(BaseTestCase):
    """Tests for GET /api/v1/documents/{id}/"""

    def test_detail_returns_200_for_valid_id(self):
        """Valid document ID should return 200"""
        response = self.client.get(f'/api/v1/documents/{self.document.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail_returns_correct_document(self):
        """Should return correct document data"""
        response = self.client.get(f'/api/v1/documents/{self.document.id}/')
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['id'], self.document.id)

    def test_detail_includes_clauses(self):
        """Detail response should include nested clauses"""
        response = self.client.get(f'/api/v1/documents/{self.document.id}/')
        data = response.json()
        self.assertIn('clauses', data['data'])
        self.assertEqual(len(data['data']['clauses']), 1)

    def test_detail_includes_risk_flags(self):
        """Detail response should include nested risk flags"""
        response = self.client.get(f'/api/v1/documents/{self.document.id}/')
        data = response.json()
        self.assertIn('risk_flags', data['data'])
        self.assertEqual(len(data['data']['risk_flags']), 1)

    def test_detail_returns_404_for_invalid_id(self):
        """Non-existent document ID should return 404"""
        response = self.client.get('/api/v1/documents/9999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ============================================================
# TEST GROUP 4: DOCUMENT UPLOAD TESTS
# ============================================================

class DocumentUploadTests(BaseTestCase):
    """Tests for POST /api/v1/documents/upload/"""

    def _make_pdf(self, name='test.pdf'):
        """Helper: creates a fresh fake PDF for each test"""
        return SimpleUploadedFile(
            name         = name,
            content      = b'%PDF-1.4 test content',
            content_type = 'application/pdf'
        )

    def test_upload_valid_pdf_returns_201(self):
        """Valid PDF upload should return 201 Created"""
        response = self.client.post(
            '/api/v1/documents/upload/',
            {
                'file':              self._make_pdf(),
                'contract_type':     'NDA',
                'counterparty_name': 'Upload Test Corp',
            },
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_upload_returns_document_data(self):
        """Upload response should return document details"""
        response = self.client.post(
            '/api/v1/documents/upload/',
            {'file': self._make_pdf()},
            format='multipart'
        )
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('id', data['data'])

    def test_upload_without_file_returns_400(self):
        """Upload without file should return 400"""
        response = self.client.post(
            '/api/v1/documents/upload/',
            {},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_non_pdf_returns_400(self):
        """Uploading non-PDF should return 400"""
        txt_file = SimpleUploadedFile(
            name         = 'document.txt',
            content      = b'This is a text file',
            content_type = 'text/plain'
        )
        response = self.client.post(
            '/api/v1/documents/upload/',
            {'file': txt_file},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_creates_document_in_db(self):
        """Upload should create a new document in database"""
        count_before = Document.objects.count()

        self.client.post(
            '/api/v1/documents/upload/',
            {'file': self._make_pdf('new_contract.pdf')},
            format='multipart'
        )

        count_after = Document.objects.count()
        self.assertEqual(count_after, count_before + 1)

    def test_uploaded_document_has_status_uploaded(self):
        """Newly uploaded document should have status=uploaded"""
        response = self.client.post(
            '/api/v1/documents/upload/',
            {'file': self._make_pdf('status_test.pdf')},
            format='multipart'
        )
        data = response.json()
        self.assertEqual(data['data']['status'], 'uploaded')


# ============================================================
# TEST GROUP 5: EXTRACTED CLAUSE TESTS
# ============================================================

class ExtractedClauseTests(BaseTestCase):
    """Tests for clause save and retrieve endpoints"""

    def test_save_single_clause_returns_201(self):
        """Saving a single clause should return 201"""
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/clauses/',
            {
                'clause_type':      'termination',
                'clause_text':      (
                    'Either party may terminate '
                    'with 30 days notice.'
                ),
                'page_number':      5,
                'confidence_score': 0.88,
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_save_clause_with_invalid_confidence_returns_400(self):
        """Clause with confidence > 1.0 should return 400"""
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/clauses/',
            {
                'clause_type':      'termination',
                'clause_text':      'Test clause text here',
                'page_number':      1,
                'confidence_score': 5.5,
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_save_clause_with_invalid_page_returns_400(self):
        """Clause with page_number = 0 should return 400"""
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/clauses/',
            {
                'clause_type':      'termination',
                'clause_text':      'Test clause text here',
                'page_number':      0,
                'confidence_score': 0.9,
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_clauses_returns_200(self):
        """GET clauses should return 200"""
        response = self.client.get(
            f'/api/v1/documents/{self.document.id}/clauses/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_save_bulk_clauses(self):
        """Saving list of clauses should work"""
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/clauses/',
            [
                {
                    'clause_type':      'termination',
                    'clause_text':      (
                        'Either party may terminate '
                        'with 30 days written notice.'
                    ),
                    'page_number':      3,
                    'confidence_score': 0.88,
                },
                {
                    'clause_type':      'governing_law',
                    'clause_text':      (
                        'This agreement is governed '
                        'by California law.'
                    ),
                    'page_number':      7,
                    'confidence_score': 0.91,
                },
            ],
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_clause_for_nonexistent_document_returns_404(self):
        """Clause for document 9999 should return 404"""
        response = self.client.post(
            '/api/v1/documents/9999/clauses/',
            {
                'clause_type':      'other',
                'clause_text':      'Some clause text here',
                'page_number':      1,
                'confidence_score': 0.5,
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ============================================================
# TEST GROUP 6: RISK FLAG TESTS
# ============================================================

class RiskFlagTests(BaseTestCase):
    """Tests for risk flag save and retrieve endpoints"""

    def test_save_single_risk_returns_201(self):
        """Saving a single risk flag should return 201"""
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/risks/',
            {
                'risk_title':       'Indemnification Risk Found',
                'flagged_text':     (
                    'The party shall indemnify and '
                    'hold harmless all parties.'
                ),
                'keyword_matched':  'indemnify',
                'severity':         'medium',
                'page_number':      3,
                'explanation':      (
                    'Broad indemnification clauses '
                    'can create unexpected liability.'
                ),
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_save_risk_with_invalid_severity_returns_400(self):
        """Risk flag with invalid severity should return 400"""
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/risks/',
            {
                'risk_title':   'Test Risk',
                'flagged_text': 'Some risky text here.',
                'severity':     'critical',
                'page_number':  1,
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_risks_returns_200(self):
        """GET risk flags should return 200"""
        response = self.client.get(
            f'/api/v1/documents/{self.document.id}/risks/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_risks_by_severity(self):
        """Filtering risks by severity should work"""
        response = self.client.get(
            f'/api/v1/documents/{self.document.id}/risks/?severity=high'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_risk_for_nonexistent_document_returns_404(self):
        """Risk flag for document 9999 should return 404"""
        response = self.client.post(
            '/api/v1/documents/9999/risks/',
            {
                'risk_title':   'Test',
                'flagged_text': 'Test text here.',
                'severity':     'low',
                'page_number':  1,
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ============================================================
# TEST GROUP 7: STATUS UPDATE TESTS
# ============================================================

class StatusUpdateTests(BaseTestCase):
    """Tests for PATCH /api/v1/documents/{id}/update-status/"""

    def test_valid_status_update_returns_200(self):
        """Valid status update should return 200"""
        response = self.client.patch(
            f'/api/v1/documents/{self.document.id}/update-status/',
            {'status': 'processing'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_status_returns_400(self):
        """Invalid status value should return 400"""
        response = self.client.patch(
            f'/api/v1/documents/{self.document.id}/update-status/',
            {'status': 'WRONG'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_body_returns_400(self):
        """Empty request body should return 400"""
        response = self.client.patch(
            f'/api/v1/documents/{self.document.id}/update-status/',
            {},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_status_actually_updates_in_db(self):
        """Status should be updated in database"""
        self.client.patch(
            f'/api/v1/documents/{self.document.id}/update-status/',
            {'status': 'completed'},
            format='json'
        )
        self.document.refresh_from_db()
        self.assertEqual(self.document.status, 'completed')

    def test_risk_score_update(self):
        """Risk score should update correctly"""
        self.client.patch(
            f'/api/v1/documents/{self.document.id}/update-status/',
            {'status': 'completed', 'risk_score': 5},
            format='json'
        )
        self.document.refresh_from_db()
        self.assertEqual(self.document.risk_score, 5)


# ============================================================
# TEST GROUP 8: STATS TESTS
# ============================================================

class StatsTests(BaseTestCase):
    """Tests for GET /api/v1/stats/"""

    def test_stats_returns_200(self):
        """Stats endpoint should return 200"""
        response = self.client.get('/api/v1/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_stats_has_required_keys(self):
        """Stats should include all required keys"""
        response = self.client.get('/api/v1/stats/')
        data     = response.json()

        required_keys = [
            'total_documents',
            'total_clauses',
            'total_risk_flags',
            'documents_by_status',
            'risks_by_severity',
            'documents_by_type',
        ]
        for key in required_keys:
            self.assertIn(key, data['data'], msg=f"Missing key: {key}")

    def test_stats_counts_are_correct(self):
        """Stats counts should match actual DB counts"""
        response = self.client.get('/api/v1/stats/')
        data     = response.json()

        self.assertEqual(
            data['data']['total_documents'],
            Document.objects.count()
        )
        self.assertEqual(
            data['data']['total_clauses'],
            ExtractedClause.objects.count()
        )


# ============================================================
# TEST GROUP 9: NLP INTEGRATION TESTS
# ============================================================

class NLPIntegrationTests(BaseTestCase):
    """Tests for NLP integration endpoints"""

    def test_pending_documents_returns_200(self):
        """Pending documents list should return 200"""
        response = self.client.get('/api/v1/nlp/documents/pending/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_pending_includes_uploaded_document(self):
        """Pending list should include our test document"""
        response = self.client.get('/api/v1/nlp/documents/pending/')
        data = response.json()
        self.assertEqual(data['data']['count'], 1)

    def test_nlp_fetch_returns_200(self):
        """NLP document fetch should return 200"""
        response = self.client.get(
            f'/api/v1/nlp/documents/{self.document.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_nlp_status_update_works(self):
        """NLP status update should work"""
        response = self.client.patch(
            f'/api/v1/nlp/documents/{self.document.id}/status/',
            {'status': 'processing'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_nlp_process_result_returns_201(self):
        """Full NLP result submission should return 201"""
        response = self.client.post(
            f'/api/v1/nlp/documents/{self.document.id}/process/',
            {
                "status":     "completed",
                "risk_score": 1,
                "metadata": {
                    "counterparty_name": "Test Corp",
                    "governing_law":     "California",
                },
                "clauses": [
                    {
                        "clause_type":      "confidentiality",
                        "clause_text":      (
                            "Both parties agree to maintain "
                            "strict confidentiality always."
                        ),
                        "page_number":      1,
                        "confidence_score": 0.9,
                    }
                ],
                "risk_flags": [
                    {
                        "risk_title":      "Test Risk",
                        "flagged_text":    (
                            "Unlimited liability clause found here."
                        ),
                        "keyword_matched": "unlimited liability",
                        "severity":        "high",
                        "page_number":     2,
                    }
                ],
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_nlp_results_returns_200(self):
        """NLP results endpoint should return 200"""
        response = self.client.get(
            f'/api/v1/nlp/documents/{self.document.id}/results/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)