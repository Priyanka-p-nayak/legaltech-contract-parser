"""
test_views.py
=============
Deep unit tests for all API views in views.py.

Tests every endpoint for:
- Correct HTTP status codes
- Response structure
- Valid data handling
- Invalid data rejection
- Edge cases
- Database state changes
"""

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

from contracts.models import Document, ExtractedClause, RiskFlag


# ============================================================
# BASE TEST CASE
# ============================================================

class BaseAPITestCase(TestCase):
    """
    Base class for all API tests.
    Creates reusable test data and helpers.
    """

    def setUp(self):
        self.client = APIClient()

        # Create test document directly in DB
        self.document = Document.objects.create(
            file_name         = 'base_test.pdf',
            contract_type     = 'NDA',
            counterparty_name = 'Base Test Corp',
            governing_law     = 'California, USA',
            status            = 'uploaded',
            risk_score        = 0,
            file_size         = 1024,
        )

        # Create test clause
        self.clause = ExtractedClause.objects.create(
            document         = self.document,
            clause_type      = 'confidentiality',
            clause_text      = (
                'Both parties agree to maintain '
                'strict confidentiality of all information.'
            ),
            page_number      = 1,
            confidence_score = 0.95,
        )

        # Create test risk flag
        self.risk = RiskFlag.objects.create(
            document        = self.document,
            risk_title      = 'Unlimited Liability Found',
            flagged_text    = (
                'The party agrees to unlimited '
                'liability for all damages.'
            ),
            keyword_matched = 'unlimited liability',
            severity        = 'high',
            page_number     = 2,
        )

    def make_pdf(self, name='test.pdf'):
        """Create a fake PDF file for upload tests."""
        return SimpleUploadedFile(
            name         = name,
            content      = b'%PDF-1.4 fake test content',
            content_type = 'application/pdf'
        )

    def make_txt(self, name='test.txt'):
        """Create a fake TXT file for invalid upload tests."""
        return SimpleUploadedFile(
            name         = name,
            content      = b'This is a text file not PDF',
            content_type = 'text/plain'
        )

    def doc_url(self, pk=None, suffix=''):
        """Build document URL."""
        if pk:
            return f'/api/v1/documents/{pk}/{suffix}'
        return '/api/v1/documents/'

    def clause_url(self, pk):
        """Build clause URL for a document."""
        return f'/api/v1/documents/{pk}/clauses/'

    def risk_url(self, pk):
        """Build risk URL for a document."""
        return f'/api/v1/documents/{pk}/risks/'


# ============================================================
# TEST GROUP 1: HEALTH CHECK ENDPOINT
# GET /api/v1/health/
# ============================================================

class HealthCheckViewTests(BaseAPITestCase):
    """Tests for GET /api/v1/health/"""

    URL = '/api/v1/health/'

    def test_returns_200(self):
        """Health check should return 200 OK."""
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_has_success_true(self):
        """Response should have success=true."""
        response = self.client.get(self.URL)
        self.assertTrue(response.json()['success'])

    def test_response_has_message(self):
        """Response should have a message field."""
        response = self.client.get(self.URL)
        self.assertIn('message', response.json())

    def test_response_has_data(self):
        """Response should have a data field."""
        response = self.client.get(self.URL)
        self.assertIn('data', response.json())

    def test_data_has_api_version(self):
        """Data should include api_version."""
        response = self.client.get(self.URL)
        self.assertIn('api_version', response.json()['data'])

    def test_data_has_correct_version_number(self):
        """api_version should be 1.0.0."""
        response = self.client.get(self.URL)
        self.assertEqual(
            response.json()['data']['api_version'],
            '1.0.0'
        )

    def test_data_has_status_healthy(self):
        """data.status should be 'healthy'."""
        response = self.client.get(self.URL)
        self.assertEqual(
            response.json()['data']['status'],
            'healthy'
        )

    def test_data_has_document_count(self):
        """Data should show total_documents count."""
        response = self.client.get(self.URL)
        self.assertIn('total_documents', response.json()['data'])

    def test_document_count_is_accurate(self):
        """total_documents count should match DB."""
        response = self.client.get(self.URL)
        self.assertEqual(
            response.json()['data']['total_documents'],
            Document.objects.count()
        )

    def test_data_has_clause_count(self):
        """Data should show total_clauses count."""
        response = self.client.get(self.URL)
        self.assertIn('total_clauses', response.json()['data'])

    def test_data_has_risk_count(self):
        """Data should show total_risk_flags count."""
        response = self.client.get(self.URL)
        self.assertIn('total_risk_flags', response.json()['data'])

    def test_data_has_endpoints_list(self):
        """Data should include list of endpoints."""
        response = self.client.get(self.URL)
        self.assertIn('endpoints', response.json()['data'])


# ============================================================
# TEST GROUP 2: DOCUMENT UPLOAD
# POST /api/v1/documents/upload/
# ============================================================

class DocumentUploadViewTests(BaseAPITestCase):
    """Tests for POST /api/v1/documents/upload/"""

    URL = '/api/v1/documents/upload/'

    def test_valid_pdf_returns_201(self):
        """Valid PDF upload should return 201 Created."""
        response = self.client.post(
            self.URL,
            {'file': self.make_pdf()},
            format='multipart'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

    def test_response_has_success_true(self):
        """Upload response should have success=true."""
        response = self.client.post(
            self.URL,
            {'file': self.make_pdf()},
            format='multipart'
        )
        self.assertTrue(response.json()['success'])

    def test_response_has_document_id(self):
        """Upload response should include document id."""
        response = self.client.post(
            self.URL,
            {'file': self.make_pdf()},
            format='multipart'
        )
        self.assertIn('id', response.json()['data'])

    def test_response_has_status_uploaded(self):
        """New document status should be 'uploaded'."""
        response = self.client.post(
            self.URL,
            {'file': self.make_pdf()},
            format='multipart'
        )
        self.assertEqual(
            response.json()['data']['status'],
            'uploaded'
        )

    def test_upload_with_contract_type(self):
        """Upload with contract_type should save it."""
        response = self.client.post(
            self.URL,
            {
                'file':          self.make_pdf(),
                'contract_type': 'MSA',
            },
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_upload_with_counterparty_name(self):
        """Upload with counterparty_name should save it."""
        response = self.client.post(
            self.URL,
            {
                'file':              self.make_pdf(),
                'counterparty_name': 'Upload Corp',
            },
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_no_file_returns_400(self):
        """Upload without file should return 400."""
        response = self.client.post(
            self.URL,
            {},
            format='multipart'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_no_file_response_has_success_false(self):
        """Upload without file should have success=false."""
        response = self.client.post(
            self.URL,
            {},
            format='multipart'
        )
        self.assertFalse(response.json()['success'])

    def test_non_pdf_returns_400(self):
        """Non-PDF file upload should return 400."""
        response = self.client.post(
            self.URL,
            {'file': self.make_txt()},
            format='multipart'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_non_pdf_has_error_message(self):
        """Non-PDF should return clear error message."""
        response = self.client.post(
            self.URL,
            {'file': self.make_txt()},
            format='multipart'
        )
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('message', data)

    def test_upload_creates_db_record(self):
        """Upload should create a new document in DB."""
        count_before = Document.objects.count()

        self.client.post(
            self.URL,
            {'file': self.make_pdf('new_upload.pdf')},
            format='multipart'
        )

        self.assertEqual(
            Document.objects.count(),
            count_before + 1
        )

    def test_upload_sets_correct_file_name(self):
        """Uploaded document should have correct file_name."""
        self.client.post(
            self.URL,
            {'file': self.make_pdf('my_contract.pdf')},
            format='multipart'
        )
        doc = Document.objects.latest('uploaded_at')
        self.assertEqual(doc.file_name, 'my_contract.pdf')

    def test_multiple_uploads_all_saved(self):
        """Multiple uploads should all be saved."""
        for i in range(3):
            self.client.post(
                self.URL,
                {'file': self.make_pdf(f'contract_{i}.pdf')},
                format='multipart'
            )

        # 3 new + 1 from setUp
        self.assertEqual(Document.objects.count(), 4)


# ============================================================
# TEST GROUP 3: DOCUMENT LIST
# GET /api/v1/documents/
# ============================================================

class DocumentListViewTests(BaseAPITestCase):
    """Tests for GET /api/v1/documents/"""

    URL = '/api/v1/documents/'

    def test_returns_200(self):
        """List should return 200 OK."""
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_has_success_true(self):
        """Response should have success=true."""
        response = self.client.get(self.URL)
        self.assertTrue(response.json()['success'])

    def test_response_has_data(self):
        """Response should have data field."""
        response = self.client.get(self.URL)
        self.assertIn('data', response.json())

    def test_pagination_present(self):
        """Response should include pagination info."""
        response = self.client.get(self.URL)
        data     = response.json()['data']
        self.assertIn('pagination', data)

    def test_pagination_has_total_count(self):
        """Pagination should include total_count."""
        response = self.client.get(self.URL)
        self.assertIn(
            'total_count',
            response.json()['data']['pagination']
        )

    def test_pagination_total_count_is_correct(self):
        """total_count should match DB document count."""
        response = self.client.get(self.URL)
        self.assertEqual(
            response.json()['data']['pagination']['total_count'],
            Document.objects.count()
        )

    def test_filter_by_status_uploaded(self):
        """Filter status=uploaded should return only uploaded docs."""
        response = self.client.get(f'{self.URL}?status=uploaded')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_status_completed(self):
        """Filter status=completed should work."""
        Document.objects.create(
            file_name='done.pdf',
            status='completed'
        )
        response = self.client.get(f'{self.URL}?status=completed')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_invalid_status_returns_400(self):
        """Filter with invalid status should return 400."""
        response = self.client.get(f'{self.URL}?status=WRONG')
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_filter_invalid_status_has_error_message(self):
        """Invalid status filter should have error message."""
        response = self.client.get(f'{self.URL}?status=WRONG')
        self.assertFalse(response.json()['success'])

    def test_search_by_filename(self):
        """Search by filename should return 200."""
        response = self.client.get(f'{self.URL}?search=base_test')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_by_counterparty(self):
        """Search by counterparty name should return 200."""
        response = self.client.get(f'{self.URL}?search=Base+Test')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_no_results(self):
        """Search with no match should return empty list."""
        response = self.client.get(
            f'{self.URL}?search=NONEXISTENTCOMPANYXYZ'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()['data']['pagination']['total_count'],
            0
        )

    def test_ordering_by_uploaded_at(self):
        """Order by uploaded_at should return 200."""
        response = self.client.get(
            f'{self.URL}?ordering=uploaded_at'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ordering_by_risk_score(self):
        """Order by risk_score should return 200."""
        response = self.client.get(
            f'{self.URL}?ordering=-risk_score'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_page_size_param(self):
        """page_size param should work."""
        response = self.client.get(
            f'{self.URL}?page=1&page_size=5'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_contract_type(self):
        """Filter by contract_type should work."""
        response = self.client.get(
            f'{self.URL}?contract_type=NDA'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_combined_filters(self):
        """Combined filters should work together."""
        response = self.client.get(
            f'{self.URL}?status=uploaded&contract_type=NDA'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ============================================================
# TEST GROUP 4: DOCUMENT DETAIL
# GET /api/v1/documents/{id}/
# ============================================================

class DocumentDetailViewTests(BaseAPITestCase):
    """Tests for GET /api/v1/documents/{id}/"""

    def test_returns_200_for_valid_id(self):
        """Valid document ID should return 200."""
        response = self.client.get(
            f'/api/v1/documents/{self.document.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_has_success_true(self):
        """Response should have success=true."""
        response = self.client.get(
            f'/api/v1/documents/{self.document.id}/'
        )
        self.assertTrue(response.json()['success'])

    def test_response_has_correct_id(self):
        """Response data should have correct document ID."""
        response = self.client.get(
            f'/api/v1/documents/{self.document.id}/'
        )
        self.assertEqual(
            response.json()['data']['id'],
            self.document.id
        )

    def test_response_has_file_name(self):
        """Response should include file_name."""
        response = self.client.get(
            f'/api/v1/documents/{self.document.id}/'
        )
        self.assertIn('file_name', response.json()['data'])

    def test_response_has_status(self):
        """Response should include status."""
        response = self.client.get(
            f'/api/v1/documents/{self.document.id}/'
        )
        self.assertIn('status', response.json()['data'])

    def test_response_has_nested_clauses(self):
        """Response should include nested clauses list."""
        response = self.client.get(
            f'/api/v1/documents/{self.document.id}/'
        )
        self.assertIn('clauses', response.json()['data'])

    def test_nested_clauses_count_is_correct(self):
        """Nested clauses count should match DB."""
        response = self.client.get(
            f'/api/v1/documents/{self.document.id}/'
        )
        self.assertEqual(
            len(response.json()['data']['clauses']),
            ExtractedClause.objects.filter(
                document=self.document
            ).count()
        )

    def test_response_has_nested_risk_flags(self):
        """Response should include nested risk_flags list."""
        response = self.client.get(
            f'/api/v1/documents/{self.document.id}/'
        )
        self.assertIn('risk_flags', response.json()['data'])

    def test_nested_risk_flags_count_is_correct(self):
        """Nested risk_flags count should match DB."""
        response = self.client.get(
            f'/api/v1/documents/{self.document.id}/'
        )
        self.assertEqual(
            len(response.json()['data']['risk_flags']),
            RiskFlag.objects.filter(
                document=self.document
            ).count()
        )

    def test_returns_404_for_nonexistent_id(self):
        """Non-existent ID should return 404."""
        response = self.client.get('/api/v1/documents/9999/')
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

    def test_returns_404_for_zero_id(self):
        """ID=0 should return 404."""
        response = self.client.get('/api/v1/documents/0/')
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

    def test_response_has_total_clauses(self):
        """Response should include total_clauses count."""
        response = self.client.get(
            f'/api/v1/documents/{self.document.id}/'
        )
        self.assertIn('total_clauses', response.json()['data'])

    def test_response_has_total_risks(self):
        """Response should include total_risks count."""
        response = self.client.get(
            f'/api/v1/documents/{self.document.id}/'
        )
        self.assertIn('total_risks', response.json()['data'])


# ============================================================
# TEST GROUP 5: DOCUMENT SUMMARY
# GET /api/v1/documents/{id}/summary/
# ============================================================

class DocumentSummaryViewTests(BaseAPITestCase):
    """Tests for GET /api/v1/documents/{id}/summary/"""

    def test_returns_200(self):
        """Summary should return 200."""
        response = self.client.get(
            f'/api/v1/documents/{self.document.id}/summary/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_has_risk_summary(self):
        """Response should include risk_summary."""
        response = self.client.get(
            f'/api/v1/documents/{self.document.id}/summary/'
        )
        self.assertIn('risk_summary', response.json()['data'])

    def test_risk_summary_has_total(self):
        """risk_summary should include total count."""
        response = self.client.get(
            f'/api/v1/documents/{self.document.id}/summary/'
        )
        self.assertIn(
            'total',
            response.json()['data']['risk_summary']
        )

    def test_risk_summary_has_severity_counts(self):
        """risk_summary should include high, medium, low counts."""
        response = self.client.get(
            f'/api/v1/documents/{self.document.id}/summary/'
        )
        summary = response.json()['data']['risk_summary']
        self.assertIn('high',   summary)
        self.assertIn('medium', summary)
        self.assertIn('low',    summary)

    def test_risk_summary_counts_are_correct(self):
        """Risk summary counts should match actual DB counts."""
        response = self.client.get(
            f'/api/v1/documents/{self.document.id}/summary/'
        )
        summary = response.json()['data']['risk_summary']

        actual_high = RiskFlag.objects.filter(
            document=self.document,
            severity='high'
        ).count()

        self.assertEqual(summary['high'], actual_high)

    def test_response_has_clause_summary(self):
        """Response should include clause_summary."""
        response = self.client.get(
            f'/api/v1/documents/{self.document.id}/summary/'
        )
        self.assertIn('clause_summary', response.json()['data'])

    def test_clause_summary_has_total(self):
        """clause_summary should include total count."""
        response = self.client.get(
            f'/api/v1/documents/{self.document.id}/summary/'
        )
        self.assertIn(
            'total',
            response.json()['data']['clause_summary']
        )

    def test_returns_404_for_nonexistent_doc(self):
        """Non-existent document should return 404."""
        response = self.client.get(
            '/api/v1/documents/9999/summary/'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )


# ============================================================
# TEST GROUP 6: DOCUMENT STATUS UPDATE
# PATCH /api/v1/documents/{id}/update-status/
# ============================================================

class DocumentStatusUpdateViewTests(BaseAPITestCase):
    """Tests for PATCH /api/v1/documents/{id}/update-status/"""

    def patch_url(self):
        return (
            f'/api/v1/documents/{self.document.id}/update-status/'
        )

    def test_valid_status_returns_200(self):
        """Valid status update should return 200."""
        response = self.client.patch(
            self.patch_url(),
            {'status': 'processing'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_status_actually_updated_in_db(self):
        """Status should be changed in database."""
        self.client.patch(
            self.patch_url(),
            {'status': 'completed'},
            format='json'
        )
        self.document.refresh_from_db()
        self.assertEqual(self.document.status, 'completed')

    def test_risk_score_update(self):
        """Risk score should be updated in database."""
        self.client.patch(
            self.patch_url(),
            {'risk_score': 7},
            format='json'
        )
        self.document.refresh_from_db()
        self.assertEqual(self.document.risk_score, 7)

    def test_counterparty_name_update(self):
        """counterparty_name should be updatable."""
        self.client.patch(
            self.patch_url(),
            {'counterparty_name': 'Updated Corp'},
            format='json'
        )
        self.document.refresh_from_db()
        self.assertEqual(
            self.document.counterparty_name,
            'Updated Corp'
        )

    def test_governing_law_update(self):
        """governing_law should be updatable."""
        self.client.patch(
            self.patch_url(),
            {'governing_law': 'New York, USA'},
            format='json'
        )
        self.document.refresh_from_db()
        self.assertEqual(
            self.document.governing_law,
            'New York, USA'
        )

    def test_all_valid_statuses_accepted(self):
        """All valid status values should be accepted."""
        for s in ['uploaded', 'processing', 'completed', 'failed']:
            response = self.client.patch(
                self.patch_url(),
                {'status': s},
                format='json'
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                msg=f"Status '{s}' should be accepted"
            )

    def test_invalid_status_returns_400(self):
        """Invalid status should return 400."""
        response = self.client.patch(
            self.patch_url(),
            {'status': 'INVALID_STATUS'},
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_empty_body_returns_400(self):
        """Empty body should return 400."""
        response = self.client.patch(
            self.patch_url(),
            {},
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_negative_risk_score_returns_400(self):
        """Negative risk_score should return 400."""
        response = self.client.patch(
            self.patch_url(),
            {'risk_score': -5},
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_nonexistent_document_returns_404(self):
        """Non-existent document ID should return 404."""
        response = self.client.patch(
            '/api/v1/documents/9999/update-status/',
            {'status': 'completed'},
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

    def test_partial_update_does_not_clear_other_fields(self):
        """PATCH should not clear other existing fields."""
        original_name = self.document.counterparty_name

        self.client.patch(
            self.patch_url(),
            {'status': 'completed'},
            format='json'
        )

        self.document.refresh_from_db()
        self.assertEqual(
            self.document.counterparty_name,
            original_name
        )


# ============================================================
# TEST GROUP 7: EXTRACTED CLAUSE ENDPOINTS
# POST /api/v1/documents/{id}/clauses/
# GET  /api/v1/documents/{id}/clauses/
# ============================================================

class ExtractedClauseViewTests(BaseAPITestCase):
    """Tests for clause save and retrieve endpoints."""

    def clause_url(self):
        return f'/api/v1/documents/{self.document.id}/clauses/'

    def valid_clause_data(self, **kwargs):
        defaults = {
            'clause_type':      'termination',
            'clause_text':      (
                'Either party may terminate this '
                'agreement with 30 days written notice.'
            ),
            'page_number':      5,
            'confidence_score': 0.88,
        }
        defaults.update(kwargs)
        return defaults

    # ── GET tests ──────────────────────────────────────────

    def test_get_clauses_returns_200(self):
        """GET clauses should return 200."""
        response = self.client.get(self.clause_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_clauses_returns_list(self):
        """GET clauses should return list."""
        response = self.client.get(self.clause_url())
        data     = response.json()['data']
        self.assertIn('clauses', data)

    def test_get_clauses_count_is_correct(self):
        """GET clauses count should match DB."""
        response = self.client.get(self.clause_url())
        data     = response.json()['data']
        self.assertEqual(
            data['total_count'],
            ExtractedClause.objects.filter(
                document=self.document
            ).count()
        )

    def test_get_clauses_filter_by_type(self):
        """GET clauses filtered by type should work."""
        response = self.client.get(
            f'{self.clause_url()}?clause_type=confidentiality'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_clauses_nonexistent_doc_returns_404(self):
        """GET clauses for non-existent doc should return 404."""
        response = self.client.get(
            '/api/v1/documents/9999/clauses/'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

    # ── POST single clause tests ───────────────────────────

    def test_post_single_clause_returns_201(self):
        """POST single clause should return 201."""
        response = self.client.post(
            self.clause_url(),
            self.valid_clause_data(),
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

    def test_post_clause_saves_to_db(self):
        """POST clause should save to database."""
        count_before = ExtractedClause.objects.filter(
            document=self.document
        ).count()

        self.client.post(
            self.clause_url(),
            self.valid_clause_data(),
            format='json'
        )

        count_after = ExtractedClause.objects.filter(
            document=self.document
        ).count()
        self.assertEqual(count_after, count_before + 1)

    def test_post_clause_has_correct_type(self):
        """Saved clause should have correct clause_type."""
        self.client.post(
            self.clause_url(),
            self.valid_clause_data(clause_type='termination'),
            format='json'
        )
        clause = ExtractedClause.objects.filter(
            document    = self.document,
            clause_type = 'termination'
        ).first()
        self.assertIsNotNone(clause)

    def test_post_clause_missing_clause_text_returns_400(self):
        """Missing clause_text should return 400."""
        data = self.valid_clause_data()
        del data['clause_text']
        response = self.client.post(
            self.clause_url(),
            data,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_post_clause_invalid_confidence_returns_400(self):
        """Invalid confidence_score should return 400."""
        response = self.client.post(
            self.clause_url(),
            self.valid_clause_data(confidence_score=5.0),
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_post_clause_invalid_page_returns_400(self):
        """Invalid page_number (0) should return 400."""
        response = self.client.post(
            self.clause_url(),
            self.valid_clause_data(page_number=0),
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_post_clause_short_text_returns_400(self):
        """Clause text shorter than 10 chars should return 400."""
        response = self.client.post(
            self.clause_url(),
            self.valid_clause_data(clause_text='Short'),
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_post_clause_nonexistent_doc_returns_404(self):
        """POST clause for non-existent doc should return 404."""
        response = self.client.post(
            '/api/v1/documents/9999/clauses/',
            self.valid_clause_data(),
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

    # ── POST bulk clause tests ─────────────────────────────

    def test_post_bulk_clauses_returns_201(self):
        """POST list of clauses should return 201."""
        response = self.client.post(
            self.clause_url(),
            [
                self.valid_clause_data(clause_type='termination'),
                self.valid_clause_data(clause_type='governing_law'),
            ],
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

    def test_post_bulk_saves_all_clauses(self):
        """Bulk POST should save all clauses."""
        count_before = ExtractedClause.objects.filter(
            document=self.document
        ).count()

        self.client.post(
            self.clause_url(),
            [
                self.valid_clause_data(clause_type='termination'),
                self.valid_clause_data(clause_type='governing_law'),
                self.valid_clause_data(clause_type='warranties'),
            ],
            format='json'
        )

        count_after = ExtractedClause.objects.filter(
            document=self.document
        ).count()
        self.assertEqual(count_after, count_before + 3)

    def test_post_empty_list_returns_400(self):
        """POST empty list should return 400."""
        response = self.client.post(
            self.clause_url(),
            [],
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )


# ============================================================
# TEST GROUP 8: RISK FLAG ENDPOINTS
# POST /api/v1/documents/{id}/risks/
# GET  /api/v1/documents/{id}/risks/
# ============================================================

class RiskFlagViewTests(BaseAPITestCase):
    """Tests for risk flag save and retrieve endpoints."""

    def risk_url(self):
        return f'/api/v1/documents/{self.document.id}/risks/'

    def valid_risk_data(self, **kwargs):
        defaults = {
            'risk_title':      'Indemnification Risk Found',
            'flagged_text':    (
                'The party shall indemnify and hold '
                'harmless all related parties without limit.'
            ),
            'keyword_matched': 'indemnify',
            'severity':        'medium',
            'page_number':     3,
            'explanation':     (
                'Broad indemnification creates liability.'
            ),
        }
        defaults.update(kwargs)
        return defaults

    # ── GET tests ──────────────────────────────────────────

    def test_get_risks_returns_200(self):
        """GET risks should return 200."""
        response = self.client.get(self.risk_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_risks_returns_list(self):
        """GET risks should return list in data."""
        response = self.client.get(self.risk_url())
        self.assertIn('risk_flags', response.json()['data'])

    def test_get_risks_count_correct(self):
        """GET risks count should match DB."""
        response = self.client.get(self.risk_url())
        data     = response.json()['data']
        self.assertEqual(
            data['total_count'],
            RiskFlag.objects.filter(
                document=self.document
            ).count()
        )

    def test_get_risks_filter_by_severity(self):
        """GET risks filter by severity should work."""
        response = self.client.get(
            f'{self.risk_url()}?severity=high'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_risks_nonexistent_doc_returns_404(self):
        """GET risks for non-existent doc should return 404."""
        response = self.client.get(
            '/api/v1/documents/9999/risks/'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

    # ── POST single risk tests ─────────────────────────────

    def test_post_single_risk_returns_201(self):
        """POST single risk should return 201."""
        response = self.client.post(
            self.risk_url(),
            self.valid_risk_data(),
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

    def test_post_risk_saves_to_db(self):
        """POST risk should save to database."""
        count_before = RiskFlag.objects.filter(
            document=self.document
        ).count()

        self.client.post(
            self.risk_url(),
            self.valid_risk_data(),
            format='json'
        )

        count_after = RiskFlag.objects.filter(
            document=self.document
        ).count()
        self.assertEqual(count_after, count_before + 1)

    def test_post_risk_all_severities_accepted(self):
        """All valid severity values should be accepted."""
        for severity in ['low', 'medium', 'high']:
            response = self.client.post(
                self.risk_url(),
                self.valid_risk_data(severity=severity),
                format='json'
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                msg=f"Severity '{severity}' should be accepted"
            )

    def test_post_risk_invalid_severity_returns_400(self):
        """Invalid severity should return 400."""
        response = self.client.post(
            self.risk_url(),
            self.valid_risk_data(severity='critical'),
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_post_risk_missing_title_returns_400(self):
        """Missing risk_title should return 400."""
        data = self.valid_risk_data()
        del data['risk_title']
        response = self.client.post(
            self.risk_url(),
            data,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_post_risk_missing_flagged_text_returns_400(self):
        """Missing flagged_text should return 400."""
        data = self.valid_risk_data()
        del data['flagged_text']
        response = self.client.post(
            self.risk_url(),
            data,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_post_risk_empty_title_returns_400(self):
        """Empty risk_title should return 400."""
        response = self.client.post(
            self.risk_url(),
            self.valid_risk_data(risk_title='   '),
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_post_risk_nonexistent_doc_returns_404(self):
        """POST risk for non-existent doc should return 404."""
        response = self.client.post(
            '/api/v1/documents/9999/risks/',
            self.valid_risk_data(),
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

    # ── POST bulk risk tests ───────────────────────────────

    def test_post_bulk_risks_returns_201(self):
        """POST list of risks should return 201."""
        response = self.client.post(
            self.risk_url(),
            [
                self.valid_risk_data(severity='high'),
                self.valid_risk_data(severity='medium'),
            ],
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

    def test_post_bulk_saves_all_risks(self):
        """Bulk POST should save all risk flags."""
        count_before = RiskFlag.objects.filter(
            document=self.document
        ).count()

        self.client.post(
            self.risk_url(),
            [
                self.valid_risk_data(risk_title='Risk 1'),
                self.valid_risk_data(risk_title='Risk 2'),
            ],
            format='json'
        )

        count_after = RiskFlag.objects.filter(
            document=self.document
        ).count()
        self.assertEqual(count_after, count_before + 2)

    def test_post_empty_list_returns_400(self):
        """POST empty list should return 400."""
        response = self.client.post(
            self.risk_url(),
            [],
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )


# ============================================================
# TEST GROUP 9: STATS ENDPOINT
# GET /api/v1/stats/
# ============================================================

class StatsViewTests(BaseAPITestCase):
    """Tests for GET /api/v1/stats/"""

    URL = '/api/v1/stats/'

    def test_returns_200(self):
        """Stats should return 200."""
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_has_success_true(self):
        """Response should have success=true."""
        response = self.client.get(self.URL)
        self.assertTrue(response.json()['success'])

    def test_has_total_documents(self):
        """Stats should include total_documents."""
        response = self.client.get(self.URL)
        self.assertIn(
            'total_documents',
            response.json()['data']
        )

    def test_has_total_clauses(self):
        """Stats should include total_clauses."""
        response = self.client.get(self.URL)
        self.assertIn(
            'total_clauses',
            response.json()['data']
        )

    def test_has_total_risk_flags(self):
        """Stats should include total_risk_flags."""
        response = self.client.get(self.URL)
        self.assertIn(
            'total_risk_flags',
            response.json()['data']
        )

    def test_has_documents_by_status(self):
        """Stats should include documents_by_status."""
        response = self.client.get(self.URL)
        self.assertIn(
            'documents_by_status',
            response.json()['data']
        )

    def test_has_risks_by_severity(self):
        """Stats should include risks_by_severity."""
        response = self.client.get(self.URL)
        self.assertIn(
            'risks_by_severity',
            response.json()['data']
        )

    def test_total_documents_is_accurate(self):
        """total_documents should match DB count."""
        response = self.client.get(self.URL)
        self.assertEqual(
            response.json()['data']['total_documents'],
            Document.objects.count()
        )

    def test_total_clauses_is_accurate(self):
        """total_clauses should match DB count."""
        response = self.client.get(self.URL)
        self.assertEqual(
            response.json()['data']['total_clauses'],
            ExtractedClause.objects.count()
        )

    def test_total_risks_is_accurate(self):
        """total_risk_flags should match DB count."""
        response = self.client.get(self.URL)
        self.assertEqual(
            response.json()['data']['total_risk_flags'],
            RiskFlag.objects.count()
        )

    def test_stats_update_after_new_document(self):
        """Stats should reflect new document after creation."""
        count_before = response = self.client.get(self.URL)
        before       = count_before.json()['data']['total_documents']

        Document.objects.create(file_name='new_stats_test.pdf')

        response_after = self.client.get(self.URL)
        after          = response_after.json()['data']['total_documents']

        self.assertEqual(after, before + 1)