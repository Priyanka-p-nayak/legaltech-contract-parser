"""
test_nlp_views.py
=================
Unit tests for all NLP integration API views.
Tests the complete NLP workflow endpoints.
"""

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

from contracts.models import Document, ExtractedClause, RiskFlag


class BaseNLPTestCase(TestCase):
    """Base class for NLP API tests."""

    def setUp(self):
        self.client = APIClient()

        self.document = Document.objects.create(
            file_name         = 'nlp_test.pdf',
            contract_type     = 'NDA',
            counterparty_name = 'NLP Test Corp',
            status            = 'uploaded',
            risk_score        = 0,
        )

    def nlp_url(self, suffix=''):
        return f'/api/v1/nlp/documents/{self.document.id}/{suffix}'

    def valid_process_payload(self, **kwargs):
        defaults = {
            "status":     "completed",
            "risk_score": 2,
            "metadata": {
                "counterparty_name":   "NLP Result Corp",
                "governing_law":       "California, USA",
                "contract_start_date": "2024-01-01",
                "contract_end_date":   "2025-12-31",
            },
            "clauses": [
                {
                    "clause_type":      "confidentiality",
                    "clause_text": (
                        "Both parties agree to maintain "
                        "strict confidentiality of all data."
                    ),
                    "page_number":      2,
                    "confidence_score": 0.95,
                }
            ],
            "risk_flags": [
                {
                    "risk_title":      "Unlimited Liability Found",
                    "flagged_text": (
                        "The vendor shall be liable for "
                        "unlimited damages from any breach."
                    ),
                    "keyword_matched": "unlimited liability",
                    "severity":        "high",
                    "page_number":     4,
                }
            ],
        }
        defaults.update(kwargs)
        return defaults


# ============================================================
# TEST GROUP 1: PENDING DOCUMENTS
# GET /api/v1/nlp/documents/pending/
# ============================================================

class NLPPendingDocumentsTests(BaseNLPTestCase):
    """Tests for GET /api/v1/nlp/documents/pending/"""

    URL = '/api/v1/nlp/documents/pending/'

    def test_returns_200(self):
        """Pending list should return 200."""
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_has_success_true(self):
        """Response should have success=true."""
        response = self.client.get(self.URL)
        self.assertTrue(response.json()['success'])

    def test_response_has_count(self):
        """Response should include count."""
        response = self.client.get(self.URL)
        self.assertIn('count', response.json()['data'])

    def test_response_has_documents_list(self):
        """Response should include documents list."""
        response = self.client.get(self.URL)
        self.assertIn('documents', response.json()['data'])

    def test_uploaded_document_in_pending(self):
        """Uploaded document should appear in pending list."""
        response = self.client.get(self.URL)
        ids      = [
            d['id'] for d in
            response.json()['data']['documents']
        ]
        self.assertIn(self.document.id, ids)

    def test_completed_document_not_in_pending(self):
        """Completed document should NOT appear in pending."""
        self.document.status = 'completed'
        self.document.save()

        response = self.client.get(self.URL)
        ids      = [
            d['id'] for d in
            response.json()['data']['documents']
        ]
        self.assertNotIn(self.document.id, ids)

    def test_processing_document_not_in_pending(self):
        """Processing document should NOT appear in pending."""
        self.document.status = 'processing'
        self.document.save()

        response = self.client.get(self.URL)
        ids      = [
            d['id'] for d in
            response.json()['data']['documents']
        ]
        self.assertNotIn(self.document.id, ids)

    def test_pending_document_has_file_name(self):
        """Each pending document should have file_name."""
        response = self.client.get(self.URL)
        docs     = response.json()['data']['documents']
        if docs:
            self.assertIn('file_name', docs[0])

    def test_pending_document_has_status(self):
        """Each pending document should have status field."""
        response = self.client.get(self.URL)
        docs     = response.json()['data']['documents']
        if docs:
            self.assertIn('status', docs[0])

    def test_empty_pending_when_all_completed(self):
        """Pending list should be empty when all docs completed."""
        Document.objects.all().update(status='completed')

        response = self.client.get(self.URL)
        data     = response.json()['data']
        self.assertEqual(data['count'], 0)


# ============================================================
# TEST GROUP 2: NLP DOCUMENT FETCH
# GET /api/v1/nlp/documents/{id}/
# ============================================================

class NLPDocumentFetchTests(BaseNLPTestCase):
    """Tests for GET /api/v1/nlp/documents/{id}/"""

    def test_returns_200_for_valid_id(self):
        """Valid document ID should return 200."""
        response = self.client.get(self.nlp_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_has_success_true(self):
        """Response should have success=true."""
        response = self.client.get(self.nlp_url())
        self.assertTrue(response.json()['success'])

    def test_response_has_document_id(self):
        """Response should include document ID."""
        response = self.client.get(self.nlp_url())
        self.assertEqual(
            response.json()['data']['id'],
            self.document.id
        )

    def test_response_has_file_name(self):
        """Response should include file_name."""
        response = self.client.get(self.nlp_url())
        self.assertIn('file_name', response.json()['data'])

    def test_response_has_status(self):
        """Response should include status."""
        response = self.client.get(self.nlp_url())
        self.assertIn('status', response.json()['data'])

    def test_response_has_processing_instructions(self):
        """Response should include processing_instructions."""
        response = self.client.get(self.nlp_url())
        self.assertIn(
            'processing_instructions',
            response.json()['data']
        )

    def test_returns_404_for_nonexistent_doc(self):
        """Non-existent document should return 404."""
        response = self.client.get(
            '/api/v1/nlp/documents/9999/'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )


# ============================================================
# TEST GROUP 3: NLP STATUS UPDATE
# PATCH /api/v1/nlp/documents/{id}/status/
# ============================================================

class NLPStatusUpdateTests(BaseNLPTestCase):
    """Tests for PATCH /api/v1/nlp/documents/{id}/status/"""

    def test_valid_status_returns_200(self):
        """Valid status update should return 200."""
        response = self.client.patch(
            self.nlp_url('status/'),
            {'status': 'processing'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_status_updated_in_db(self):
        """Status should be updated in database."""
        self.client.patch(
            self.nlp_url('status/'),
            {'status': 'processing'},
            format='json'
        )
        self.document.refresh_from_db()
        self.assertEqual(self.document.status, 'processing')

    def test_response_has_old_and_new_status(self):
        """Response should show old and new status."""
        response = self.client.patch(
            self.nlp_url('status/'),
            {'status': 'processing'},
            format='json'
        )
        data = response.json()['data']
        self.assertIn('old_status', data)
        self.assertIn('new_status', data)

    def test_old_status_is_correct(self):
        """old_status should reflect previous status."""
        response = self.client.patch(
            self.nlp_url('status/'),
            {'status': 'processing'},
            format='json'
        )
        self.assertEqual(
            response.json()['data']['old_status'],
            'uploaded'
        )

    def test_new_status_is_correct(self):
        """new_status should reflect updated status."""
        response = self.client.patch(
            self.nlp_url('status/'),
            {'status': 'processing'},
            format='json'
        )
        self.assertEqual(
            response.json()['data']['new_status'],
            'processing'
        )

    def test_invalid_status_returns_400(self):
        """Invalid status value should return 400."""
        response = self.client.patch(
            self.nlp_url('status/'),
            {'status': 'INVALID'},
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_missing_status_returns_400(self):
        """Missing status field should return 400."""
        response = self.client.patch(
            self.nlp_url('status/'),
            {'other_field': 'value'},
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_empty_body_returns_400(self):
        """Empty body should return 400."""
        response = self.client.patch(
            self.nlp_url('status/'),
            {},
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_nonexistent_doc_returns_404(self):
        """Non-existent document should return 404."""
        response = self.client.patch(
            '/api/v1/nlp/documents/9999/status/',
            {'status': 'processing'},
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )


# ============================================================
# TEST GROUP 4: NLP PROCESS RESULT
# POST /api/v1/nlp/documents/{id}/process/
# ============================================================

class NLPProcessResultTests(BaseNLPTestCase):
    """Tests for POST /api/v1/nlp/documents/{id}/process/"""

    def test_valid_payload_returns_201(self):
        """Valid NLP results should return 201."""
        response = self.client.post(
            self.nlp_url('process/'),
            self.valid_process_payload(),
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

    def test_response_has_success_true(self):
        """Response should have success=true."""
        response = self.client.post(
            self.nlp_url('process/'),
            self.valid_process_payload(),
            format='json'
        )
        self.assertTrue(response.json()['success'])

    def test_document_status_updated(self):
        """Document status should be updated in DB."""
        self.client.post(
            self.nlp_url('process/'),
            self.valid_process_payload(status='completed'),
            format='json'
        )
        self.document.refresh_from_db()
        self.assertEqual(self.document.status, 'completed')

    def test_risk_score_updated(self):
        """Risk score should be updated in DB."""
        self.client.post(
            self.nlp_url('process/'),
            self.valid_process_payload(risk_score=5),
            format='json'
        )
        self.document.refresh_from_db()
        self.assertEqual(self.document.risk_score, 5)

    def test_metadata_saved_to_db(self):
        """Metadata should be saved to document."""
        self.client.post(
            self.nlp_url('process/'),
            self.valid_process_payload(),
            format='json'
        )
        self.document.refresh_from_db()
        self.assertEqual(
            self.document.counterparty_name,
            'NLP Result Corp'
        )
        self.assertEqual(
            self.document.governing_law,
            'California, USA'
        )

    def test_clauses_saved_to_db(self):
        """Clauses should be saved to database."""
        self.client.post(
            self.nlp_url('process/'),
            self.valid_process_payload(),
            format='json'
        )
        count = ExtractedClause.objects.filter(
            document=self.document
        ).count()
        self.assertEqual(count, 1)

    def test_risk_flags_saved_to_db(self):
        """Risk flags should be saved to database."""
        self.client.post(
            self.nlp_url('process/'),
            self.valid_process_payload(),
            format='json'
        )
        count = RiskFlag.objects.filter(
            document=self.document
        ).count()
        self.assertEqual(count, 1)

    def test_response_has_total_clauses(self):
        """Response should include total_clauses count."""
        response = self.client.post(
            self.nlp_url('process/'),
            self.valid_process_payload(),
            format='json'
        )
        self.assertIn('total_clauses', response.json()['data'])

    def test_response_has_total_risks(self):
        """Response should include total_risks count."""
        response = self.client.post(
            self.nlp_url('process/'),
            self.valid_process_payload(),
            format='json'
        )
        self.assertIn('total_risks', response.json()['data'])

    def test_reprocessing_completed_doc_returns_409(self):
        """Re-processing completed document should return 409 Conflict."""
        self.document.status = 'completed'
        self.document.save()

        response = self.client.post(
            self.nlp_url('process/'),
            self.valid_process_payload(),
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_409_CONFLICT,
            msg="Re-processing completed doc should return 409 Conflict"
        )

    def test_empty_clauses_and_risks_accepted(self):
        """Empty clauses and risks lists should be accepted."""
        payload  = self.valid_process_payload()
        payload['clauses']    = []
        payload['risk_flags'] = []

        response = self.client.post(
            self.nlp_url('process/'),
            payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

    def test_nonexistent_doc_returns_404(self):
        """Non-existent document should return 404."""
        response = self.client.post(
            '/api/v1/nlp/documents/9999/process/',
            self.valid_process_payload(),
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

    def test_multiple_clauses_and_risks_saved(self):
        """Multiple clauses and risks should all be saved."""
        payload = {
            "status":     "completed",
            "risk_score": 3,
            "metadata":   {},
            "clauses": [
                {
                    "clause_type":      "confidentiality",
                    "clause_text":      "Confidentiality clause text here.",
                    "page_number":      1,
                    "confidence_score": 0.9,
                },
                {
                    "clause_type":      "termination",
                    "clause_text":      "Termination clause text details.",
                    "page_number":      2,
                    "confidence_score": 0.85,
                },
                {
                    "clause_type":      "governing_law",
                    "clause_text":      "Governing law clause text here.",
                    "page_number":      3,
                    "confidence_score": 0.92,
                },
            ],
            "risk_flags": [
                {
                    "risk_title":   "Risk 1",
                    "flagged_text": "Unlimited liability clause found.",
                    "severity":     "high",
                    "page_number":  2,
                },
                {
                    "risk_title":   "Risk 2",
                    "flagged_text": "Exclusive rights clause found here.",
                    "severity":     "medium",
                    "page_number":  4,
                },
            ],
        }

        response = self.client.post(
            self.nlp_url('process/'),
            payload,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        data = response.json()['data']
        self.assertEqual(data['total_clauses'], 3)
        self.assertEqual(data['total_risks'],   2)


# ============================================================
# TEST GROUP 5: NLP RESULTS
# GET /api/v1/nlp/documents/{id}/results/
# ============================================================

class NLPResultsTests(BaseNLPTestCase):
    """Tests for GET /api/v1/nlp/documents/{id}/results/"""

    def setUp(self):
        super().setUp()

        # Add clauses and risks for testing
        ExtractedClause.objects.create(
            document         = self.document,
            clause_type      = 'confidentiality',
            clause_text      = (
                'Both parties agree to maintain confidentiality.'
            ),
            page_number      = 1,
            confidence_score = 0.95,
        )
        RiskFlag.objects.create(
            document     = self.document,
            risk_title   = 'Test Risk',
            flagged_text = 'Some risky text found here.',
            severity     = 'high',
            page_number  = 2,
        )

    def test_returns_200(self):
        """NLP results should return 200."""
        response = self.client.get(self.nlp_url('results/'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_has_clauses(self):
        """Response should include clauses section."""
        response = self.client.get(self.nlp_url('results/'))
        self.assertIn('clauses', response.json()['data'])

    def test_response_has_risk_flags(self):
        """Response should include risk_flags section."""
        response = self.client.get(self.nlp_url('results/'))
        self.assertIn('risk_flags', response.json()['data'])

    def test_clauses_grouped_by_type(self):
        """Clauses should be grouped by type."""
        response = self.client.get(self.nlp_url('results/'))
        self.assertIn(
            'by_type',
            response.json()['data']['clauses']
        )

    def test_risks_grouped_by_severity(self):
        """Risks should be grouped by severity."""
        response = self.client.get(self.nlp_url('results/'))
        self.assertIn(
            'by_severity',
            response.json()['data']['risk_flags']
        )

    def test_severity_groups_have_correct_keys(self):
        """Severity groups should have high/medium/low keys."""
        response    = self.client.get(self.nlp_url('results/'))
        by_severity = response.json()['data']['risk_flags']['by_severity']
        self.assertIn('high',   by_severity)
        self.assertIn('medium', by_severity)
        self.assertIn('low',    by_severity)

    def test_clause_total_count_correct(self):
        """Clauses total count should match DB."""
        response = self.client.get(self.nlp_url('results/'))
        self.assertEqual(
            response.json()['data']['clauses']['total'],
            ExtractedClause.objects.filter(
                document=self.document
            ).count()
        )

    def test_risk_total_count_correct(self):
        """Risk flags total count should match DB."""
        response = self.client.get(self.nlp_url('results/'))
        self.assertEqual(
            response.json()['data']['risk_flags']['total'],
            RiskFlag.objects.filter(
                document=self.document
            ).count()
        )

    def test_has_unresolved_count(self):
        """Response should include unresolved risk count."""
        response = self.client.get(self.nlp_url('results/'))
        self.assertIn(
            'unresolved',
            response.json()['data']['risk_flags']
        )

    def test_has_resolved_count(self):
        """Response should include resolved risk count."""
        response = self.client.get(self.nlp_url('results/'))
        self.assertIn(
            'resolved',
            response.json()['data']['risk_flags']
        )

    def test_returns_404_for_nonexistent_doc(self):
        """Non-existent document should return 404."""
        response = self.client.get(
            '/api/v1/nlp/documents/9999/results/'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )