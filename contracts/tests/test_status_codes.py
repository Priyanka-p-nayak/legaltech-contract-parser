"""
test_status_codes.py
====================
Tests that verify EVERY endpoint returns the
EXACT correct HTTP status code.

This is critical for API quality and review.
"""

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

from contracts.models import Document, ExtractedClause, RiskFlag


class BaseStatusCodeTest(TestCase):
    """Base class for status code tests."""

    def setUp(self):
        self.client = APIClient()

        self.document = Document.objects.create(
            file_name         = 'status_test.pdf',
            contract_type     = 'NDA',
            counterparty_name = 'Status Test Corp',
            status            = 'uploaded',
            risk_score        = 0,
        )

        self.completed_doc = Document.objects.create(
            file_name  = 'completed_test.pdf',
            status     = 'completed',
            risk_score = 2,
        )

        self.clause = ExtractedClause.objects.create(
            document         = self.document,
            clause_type      = 'confidentiality',
            clause_text      = (
                'Both parties agree to maintain confidentiality.'
            ),
            page_number      = 1,
            confidence_score = 0.95,
        )

        self.risk = RiskFlag.objects.create(
            document     = self.document,
            risk_title   = 'Test Risk',
            flagged_text = 'Some risky text found here.',
            severity     = 'high',
            page_number  = 1,
        )

    def make_pdf(self, name='test.pdf'):
        return SimpleUploadedFile(
            name         = name,
            content      = b'%PDF-1.4 content',
            content_type = 'application/pdf'
        )

    def make_txt(self):
        return SimpleUploadedFile(
            name         = 'test.txt',
            content      = b'text content',
            content_type = 'text/plain'
        )


# ============================================================
# TEST GROUP 1: UTILITY ENDPOINTS
# ============================================================

class UtilityStatusCodeTests(BaseStatusCodeTest):
    """Status codes for utility endpoints."""

    def test_health_check_returns_200(self):
        """GET /api/v1/health/ → 200 OK"""
        response = self.client.get('/api/v1/health/')
        self.assertEqual(response.status_code, 200)

    def test_stats_returns_200(self):
        """GET /api/v1/stats/ → 200 OK"""
        response = self.client.get('/api/v1/stats/')
        self.assertEqual(response.status_code, 200)


# ============================================================
# TEST GROUP 2: DOCUMENT UPLOAD STATUS CODES
# ============================================================

class DocumentUploadStatusCodeTests(BaseStatusCodeTest):
    """Status codes for POST /api/v1/documents/upload/"""

    URL = '/api/v1/documents/upload/'

    def test_valid_upload_returns_201(self):
        """
        201 Created — successful PDF upload.
        """
        response = self.client.post(
            self.URL,
            {'file': self.make_pdf()},
            format='multipart'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            msg="Valid upload should return 201 Created"
        )

    def test_no_file_returns_400(self):
        """
        400 Bad Request — no file provided.
        """
        response = self.client.post(
            self.URL,
            {},
            format='multipart'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            msg="Missing file should return 400"
        )

    def test_non_pdf_returns_400(self):
        """
        400 Bad Request — file is not a PDF.
        """
        response = self.client.post(
            self.URL,
            {'file': self.make_txt()},
            format='multipart'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            msg="Non-PDF file should return 400"
        )

    def test_empty_file_returns_400(self):
        """
        400 Bad Request — file is empty (0 bytes).
        """
        empty_pdf = SimpleUploadedFile(
            name         = 'empty.pdf',
            content      = b'',
            content_type = 'application/pdf'
        )
        response = self.client.post(
            self.URL,
            {'file': empty_pdf},
            format='multipart'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            msg="Empty file should return 400"
        )

    def test_response_has_status_code_field(self):
        """
        Response body should include status_code field.
        """
        response = self.client.post(
            self.URL,
            {'file': self.make_pdf()},
            format='multipart'
        )
        self.assertIn('status_code', response.json())
        self.assertEqual(
            response.json()['status_code'],
            201
        )

    def test_error_response_has_status_code_field(self):
        """
        Error response should also include status_code field.
        """
        response = self.client.post(
            self.URL,
            {},
            format='multipart'
        )
        self.assertIn('status_code', response.json())
        self.assertEqual(
            response.json()['status_code'],
            400
        )


# ============================================================
# TEST GROUP 3: DOCUMENT LIST STATUS CODES
# ============================================================

class DocumentListStatusCodeTests(BaseStatusCodeTest):
    """Status codes for GET /api/v1/documents/"""

    URL = '/api/v1/documents/'

    def test_get_list_returns_200(self):
        """200 OK — successful list retrieval."""
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, 200)

    def test_invalid_status_filter_returns_400(self):
        """400 Bad Request — invalid status filter."""
        response = self.client.get(
            f'{self.URL}?status=INVALID'
        )
        self.assertEqual(response.status_code, 400)

    def test_valid_status_filter_returns_200(self):
        """200 OK — valid status filter."""
        for s in ['uploaded', 'processing', 'completed', 'failed']:
            response = self.client.get(f'{self.URL}?status={s}')
            self.assertEqual(
                response.status_code,
                200,
                msg=f"Status filter '{s}' should return 200"
            )


# ============================================================
# TEST GROUP 4: DOCUMENT DETAIL STATUS CODES
# ============================================================

class DocumentDetailStatusCodeTests(BaseStatusCodeTest):
    """Status codes for GET /api/v1/documents/{id}/"""

    def test_valid_id_returns_200(self):
        """200 OK — document found."""
        response = self.client.get(
            f'/api/v1/documents/{self.document.id}/'
        )
        self.assertEqual(response.status_code, 200)

    def test_invalid_id_returns_404(self):
        """404 Not Found — document does not exist."""
        response = self.client.get('/api/v1/documents/99999/')
        self.assertEqual(response.status_code, 404)

    def test_summary_valid_id_returns_200(self):
        """200 OK — summary for valid document."""
        response = self.client.get(
            f'/api/v1/documents/{self.document.id}/summary/'
        )
        self.assertEqual(response.status_code, 200)

    def test_summary_invalid_id_returns_404(self):
        """404 Not Found — summary for non-existent document."""
        response = self.client.get(
            '/api/v1/documents/99999/summary/'
        )
        self.assertEqual(response.status_code, 404)


# ============================================================
# TEST GROUP 5: STATUS UPDATE STATUS CODES
# ============================================================

class StatusUpdateStatusCodeTests(BaseStatusCodeTest):
    """Status codes for PATCH /api/v1/documents/{id}/update-status/"""

    def patch_url(self, doc_id=None):
        doc_id = doc_id or self.document.id
        return f'/api/v1/documents/{doc_id}/update-status/'

    def test_valid_update_returns_200(self):
        """200 OK — valid status update."""
        response = self.client.patch(
            self.patch_url(),
            {'status': 'processing'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)

    def test_invalid_status_returns_400(self):
        """400 Bad Request — invalid status value."""
        response = self.client.patch(
            self.patch_url(),
            {'status': 'WRONG'},
            format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_empty_body_returns_400(self):
        """400 Bad Request — empty request body."""
        response = self.client.patch(
            self.patch_url(),
            {},
            format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_nonexistent_doc_returns_404(self):
        """404 Not Found — document not found."""
        response = self.client.patch(
            self.patch_url(doc_id=99999),
            {'status': 'completed'},
            format='json'
        )
        self.assertEqual(response.status_code, 404)

    def test_negative_risk_score_returns_400(self):
        """400 Bad Request — negative risk score."""
        response = self.client.patch(
            self.patch_url(),
            {'risk_score': -1},
            format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_date_format_returns_400(self):
        """400 Bad Request — wrong date format."""
        response = self.client.patch(
            self.patch_url(),
            {
                'status':              'completed',
                'contract_start_date': '01-01-2024',
            },
            format='json'
        )
        self.assertEqual(response.status_code, 400)


# ============================================================
# TEST GROUP 6: CLAUSE ENDPOINT STATUS CODES
# ============================================================

class ClauseStatusCodeTests(BaseStatusCodeTest):
    """Status codes for clause endpoints."""

    def clause_url(self, doc_id=None):
        doc_id = doc_id or self.document.id
        return f'/api/v1/documents/{doc_id}/clauses/'

    def valid_clause(self):
        return {
            'clause_type':      'termination',
            'clause_text':      (
                'Either party may terminate this '
                'agreement with 30 days written notice.'
            ),
            'page_number':      3,
            'confidence_score': 0.88,
        }

    def test_get_clauses_returns_200(self):
        """200 OK — get clauses for valid document."""
        response = self.client.get(self.clause_url())
        self.assertEqual(response.status_code, 200)

    def test_get_clauses_invalid_doc_returns_404(self):
        """404 Not Found — get clauses for non-existent doc."""
        response = self.client.get(self.clause_url(doc_id=99999))
        self.assertEqual(response.status_code, 404)

    def test_post_valid_clause_returns_201(self):
        """201 Created — valid clause saved."""
        response = self.client.post(
            self.clause_url(),
            self.valid_clause(),
            format='json'
        )
        self.assertEqual(response.status_code, 201)

    def test_post_invalid_confidence_returns_400(self):
        """400 Bad Request — confidence score out of range."""
        data = self.valid_clause()
        data['confidence_score'] = 2.0
        response = self.client.post(
            self.clause_url(),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_post_invalid_page_returns_400(self):
        """400 Bad Request — page number is 0."""
        data = self.valid_clause()
        data['page_number'] = 0
        response = self.client.post(
            self.clause_url(),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_post_short_text_returns_400(self):
        """400 Bad Request — clause text too short."""
        data = self.valid_clause()
        data['clause_text'] = 'Short'
        response = self.client.post(
            self.clause_url(),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_post_empty_list_returns_400(self):
        """400 Bad Request — empty bulk list."""
        response = self.client.post(
            self.clause_url(),
            [],
            format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_post_bulk_valid_returns_201(self):
        """201 Created — valid bulk clauses."""
        response = self.client.post(
            self.clause_url(),
            [self.valid_clause(), self.valid_clause()],
            format='json'
        )
        self.assertEqual(response.status_code, 201)

    def test_post_clause_invalid_doc_returns_404(self):
        """404 Not Found — clause for non-existent doc."""
        response = self.client.post(
            self.clause_url(doc_id=99999),
            self.valid_clause(),
            format='json'
        )
        self.assertEqual(response.status_code, 404)


# ============================================================
# TEST GROUP 7: RISK FLAG STATUS CODES
# ============================================================

class RiskFlagStatusCodeTests(BaseStatusCodeTest):
    """Status codes for risk flag endpoints."""

    def risk_url(self, doc_id=None):
        doc_id = doc_id or self.document.id
        return f'/api/v1/documents/{doc_id}/risks/'

    def valid_risk(self):
        return {
            'risk_title':   'Indemnification Risk',
            'flagged_text': (
                'The party shall indemnify all '
                'related parties without limit.'
            ),
            'severity':     'medium',
            'page_number':  3,
        }

    def test_get_risks_returns_200(self):
        """200 OK — get risks for valid document."""
        response = self.client.get(self.risk_url())
        self.assertEqual(response.status_code, 200)

    def test_get_risks_invalid_doc_returns_404(self):
        """404 Not Found — risks for non-existent doc."""
        response = self.client.get(self.risk_url(doc_id=99999))
        self.assertEqual(response.status_code, 404)

    def test_post_valid_risk_returns_201(self):
        """201 Created — valid risk flag saved."""
        response = self.client.post(
            self.risk_url(),
            self.valid_risk(),
            format='json'
        )
        self.assertEqual(response.status_code, 201)

    def test_post_invalid_severity_returns_400(self):
        """400 Bad Request — invalid severity."""
        data = self.valid_risk()
        data['severity'] = 'critical'
        response = self.client.post(
            self.risk_url(),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_post_empty_title_returns_400(self):
        """400 Bad Request — empty risk title."""
        data = self.valid_risk()
        data['risk_title'] = '   '
        response = self.client.post(
            self.risk_url(),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_post_empty_list_returns_400(self):
        """400 Bad Request — empty bulk list."""
        response = self.client.post(
            self.risk_url(),
            [],
            format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_post_bulk_valid_returns_201(self):
        """201 Created — valid bulk risks."""
        response = self.client.post(
            self.risk_url(),
            [self.valid_risk(), self.valid_risk()],
            format='json'
        )
        self.assertEqual(response.status_code, 201)

    def test_post_risk_invalid_doc_returns_404(self):
        """404 Not Found — risk for non-existent doc."""
        response = self.client.post(
            self.risk_url(doc_id=99999),
            self.valid_risk(),
            format='json'
        )
        self.assertEqual(response.status_code, 404)


# ============================================================
# TEST GROUP 8: NLP ENDPOINT STATUS CODES
# ============================================================

class NLPStatusCodeTests(BaseStatusCodeTest):
    """Status codes for NLP integration endpoints."""

    def nlp_url(self, suffix='', doc_id=None):
        doc_id = doc_id or self.document.id
        return f'/api/v1/nlp/documents/{doc_id}/{suffix}'

    def valid_payload(self):
        return {
            "status":     "completed",
            "risk_score": 1,
            "metadata":   {},
            "clauses": [
                {
                    "clause_type":      "other",
                    "clause_text":      "Test clause text here.",
                    "page_number":      1,
                    "confidence_score": 0.9,
                }
            ],
            "risk_flags": [
                {
                    "risk_title":   "Test Risk",
                    "flagged_text": "Some risky text here found.",
                    "severity":     "low",
                    "page_number":  1,
                }
            ],
        }

    def test_pending_returns_200(self):
        """200 OK — pending documents list."""
        response = self.client.get(
            '/api/v1/nlp/documents/pending/'
        )
        self.assertEqual(response.status_code, 200)

    def test_fetch_doc_returns_200(self):
        """200 OK — fetch document for NLP."""
        response = self.client.get(self.nlp_url())
        self.assertEqual(response.status_code, 200)

    def test_fetch_nonexistent_returns_404(self):
        """404 Not Found — fetch non-existent document."""
        response = self.client.get(
            self.nlp_url(doc_id=99999)
        )
        self.assertEqual(response.status_code, 404)

    def test_status_update_returns_200(self):
        """200 OK — valid status update."""
        response = self.client.patch(
            self.nlp_url('status/'),
            {'status': 'processing'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)

    def test_status_update_invalid_returns_400(self):
        """400 Bad Request — invalid status value."""
        response = self.client.patch(
            self.nlp_url('status/'),
            {'status': 'WRONG'},
            format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_status_update_nonexistent_returns_404(self):
        """404 Not Found — update non-existent document."""
        response = self.client.patch(
            self.nlp_url('status/', doc_id=99999),
            {'status': 'processing'},
            format='json'
        )
        self.assertEqual(response.status_code, 404)

    def test_process_returns_201(self):
        """201 Created — valid NLP results submission."""
        response = self.client.post(
            self.nlp_url('process/'),
            self.valid_payload(),
            format='json'
        )
        self.assertEqual(response.status_code, 201)

    def test_process_already_completed_returns_409(self):
        """
        409 Conflict — document already processed.
        Re-processing a completed document is a conflict.
        """
        response = self.client.post(
            f'/api/v1/nlp/documents/{self.completed_doc.id}/process/',
            self.valid_payload(),
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_409_CONFLICT,
            msg="Re-processing completed doc should return 409 Conflict"
        )

    def test_process_invalid_status_returns_400(self):
        """400 Bad Request — invalid status in payload."""
        payload          = self.valid_payload()
        payload['status'] = 'INVALID'
        response          = self.client.post(
            self.nlp_url('process/'),
            payload,
            format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_process_nonexistent_doc_returns_404(self):
        """404 Not Found — process non-existent document."""
        response = self.client.post(
            self.nlp_url('process/', doc_id=99999),
            self.valid_payload(),
            format='json'
        )
        self.assertEqual(response.status_code, 404)

    def test_results_returns_200(self):
        """200 OK — get NLP results."""
        response = self.client.get(self.nlp_url('results/'))
        self.assertEqual(response.status_code, 200)

    def test_results_nonexistent_returns_404(self):
        """404 Not Found — results for non-existent doc."""
        response = self.client.get(
            self.nlp_url('results/', doc_id=99999)
        )
        self.assertEqual(response.status_code, 404)


# ============================================================
# TEST GROUP 9: ERROR MESSAGE QUALITY TESTS
# ============================================================

class ErrorMessageQualityTests(BaseStatusCodeTest):
    """
    Tests that error messages are clear and helpful.
    Every error should tell user what went wrong
    and ideally what to do to fix it.
    """

    def test_no_file_message_mentions_file_field(self):
        """
        Error for missing file should mention 'file' field.
        """
        response = self.client.post(
            '/api/v1/documents/upload/',
            {},
            format='multipart'
        )
        message = response.json()['message'].lower()
        self.assertTrue(
            'file' in message,
            msg="Error message should mention 'file' field"
        )

    def test_invalid_status_message_shows_allowed_values(self):
        """
        Error for invalid status should list allowed values.
        """
        response = self.client.get(
            '/api/v1/documents/?status=WRONG'
        )
        message = response.json()['message'].lower()
        # Should mention at least one valid status
        self.assertTrue(
            'uploaded' in message or 'allowed' in message,
            msg="Error should show allowed status values"
        )

    def test_404_message_is_informative(self):
        """
        404 error should have a clear message.
        """
        response = self.client.get('/api/v1/documents/99999/')
        data     = response.json()
        self.assertIn('message', data)
        self.assertIsNotNone(data['message'])
        self.assertGreater(len(data['message']), 5)

    def test_all_errors_have_success_false(self):
        """
        ALL error responses must have success=false.
        """
        error_responses = [
            self.client.get('/api/v1/documents/99999/'),
            self.client.post(
                '/api/v1/documents/upload/',
                {},
                format='multipart'
            ),
            self.client.get(
                '/api/v1/documents/?status=INVALID'
            ),
        ]

        for response in error_responses:
            self.assertFalse(
                response.json()['success'],
                msg=(
                    f"Error response {response.status_code} "
                    f"should have success=false"
                )
            )

    def test_all_errors_have_message_field(self):
        """
        ALL error responses must have a message field.
        """
        error_responses = [
            self.client.get('/api/v1/documents/99999/'),
            self.client.post(
                '/api/v1/documents/upload/',
                {},
                format='multipart'
            ),
            self.client.get(
                '/api/v1/documents/?status=INVALID'
            ),
        ]

        for response in error_responses:
            self.assertIn(
                'message',
                response.json(),
                msg="All error responses must have 'message' field"
            )

    def test_all_errors_have_status_code_field(self):
        """
        ALL error responses must have a status_code field.
        """
        error_responses = [
            self.client.get('/api/v1/documents/99999/'),
            self.client.post(
                '/api/v1/documents/upload/',
                {},
                format='multipart'
            ),
        ]

        for response in error_responses:
            self.assertIn(
                'status_code',
                response.json(),
                msg="All error responses must have 'status_code' field"
            )

    def test_success_responses_have_success_true(self):
        """
        ALL success responses must have success=true.
        """
        success_responses = [
            self.client.get('/api/v1/health/'),
            self.client.get('/api/v1/stats/'),
            self.client.get('/api/v1/documents/'),
            self.client.get(
                f'/api/v1/documents/{self.document.id}/'
            ),
        ]

        for response in success_responses:
            self.assertTrue(
                response.json()['success'],
                msg=(
                    f"Success response {response.status_code} "
                    f"should have success=true"
                )
            )