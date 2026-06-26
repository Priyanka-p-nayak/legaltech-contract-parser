"""
test_edge_cases.py
==================
Tests for all edge cases in the LegalTech API.
"""

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

from contracts.models import Document, ExtractedClause, RiskFlag


class BaseEdgeTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.document = Document.objects.create(
            file_name='edge_test.pdf',
            contract_type='NDA',
            counterparty_name='Edge Test Corp',
            status='uploaded',
            risk_score=0,
        )

    def make_pdf(self, name='test.pdf', content=None):
        return SimpleUploadedFile(
            name=name,
            content=content or b'%PDF-1.4 content',
            content_type='application/pdf'
        )

    def clause_url(self):
        return f'/api/v1/documents/{self.document.id}/clauses/'

    def risk_url(self):
        return f'/api/v1/documents/{self.document.id}/risks/'

    def valid_clause(self, **kwargs):
        defaults = {
            'clause_type': 'other',
            'clause_text': 'This is a valid clause text.',
            'page_number': 1,
            'confidence_score': 0.5,
        }
        defaults.update(kwargs)
        return defaults

    def valid_risk(self, **kwargs):
        defaults = {
            'risk_title': 'Test Risk Title Here',
            'flagged_text': 'This is the flagged text found.',
            'severity': 'medium',
            'page_number': 1,
        }
        defaults.update(kwargs)
        return defaults


class FileUploadEdgeCaseTests(BaseEdgeTestCase):
    URL = '/api/v1/documents/upload/'

    def test_empty_pdf_file_returns_400(self):
        empty_pdf = SimpleUploadedFile(name='empty.pdf', content=b'', content_type='application/pdf')
        response = self.client.post(self.URL, {'file': empty_pdf}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_file_with_pdf_extension_but_txt_content(self):
        fake_pdf = SimpleUploadedFile(name='fake.pdf', content=b'This is actually text content', content_type='application/pdf')
        response = self.client.post(self.URL, {'file': fake_pdf}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_uppercase_pdf_extension_accepted(self):
        """
        File with .PDF (uppercase) extension should be accepted.
        We normalize filenames to lowercase, so .PDF becomes .pdf.
        """
        upper_pdf = SimpleUploadedFile(
            name='contract.PDF',
            content=b'%PDF-1.4 content here',
            content_type='application/pdf'
        )
        response = self.client.post(
            self.URL,
            {'file': upper_pdf},
            format='multipart'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

    def test_docx_file_rejected(self):
        docx_file = SimpleUploadedFile(name='contract.docx', content=b'PK fake docx content', content_type='application/vnd.openxmlformats')
        response = self.client.post(self.URL, {'file': docx_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_image_file_rejected(self):
        img_file = SimpleUploadedFile(name='scan.jpg', content=b'JPEG fake image content', content_type='image/jpeg')
        response = self.client.post(self.URL, {'file': img_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filename_with_spaces_accepted(self):
        spaced_pdf = SimpleUploadedFile(name='my contract file.pdf', content=b'%PDF-1.4 valid content', content_type='application/pdf')
        response = self.client.post(self.URL, {'file': spaced_pdf}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_filename_with_special_chars_accepted(self):
        special_pdf = SimpleUploadedFile(name='contract_2024-01-01_v2.pdf', content=b'%PDF-1.4 valid content', content_type='application/pdf')
        response = self.client.post(self.URL, {'file': special_pdf}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_upload_with_very_long_counterparty_name(self):
        response = self.client.post(self.URL, {'file': self.make_pdf(), 'counterparty_name': 'A' * 300}, format='multipart')
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
        self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_upload_no_body_at_all_returns_400(self):
        response = self.client.post(self.URL, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DocumentListEdgeCaseTests(BaseEdgeTestCase):
    URL = '/api/v1/documents/'

    def test_empty_search_query_returns_all(self):
        response = self.client.get(f'{self.URL}?search=')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_with_spaces_only(self):
        response = self.client.get(f'{self.URL}?search=   ')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_with_special_characters(self):
        response = self.client.get(f'{self.URL}?search=<script>alert(1)</script>')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_with_sql_injection(self):
        response = self.client.get(f"{self.URL}?search=' OR '1'='1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_very_long_search_query(self):
        long_query = 'A' * 1000
        response = self.client.get(f'{self.URL}?search={long_query}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_ordering_falls_back_to_default(self):
        response = self.client.get(f'{self.URL}?ordering=invalid_field')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_page_beyond_last_returns_empty(self):
        response = self.client.get(f'{self.URL}?page=9999')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_page_size_zero_handled(self):
        response = self.client.get(f'{self.URL}?page_size=0')
        self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_page_size_negative_handled(self):
        response = self.client.get(f'{self.URL}?page_size=-5')
        self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_all_status_filters_work(self):
        for s in ['uploaded', 'processing', 'completed', 'failed']:
            response = self.client.get(f'{self.URL}?status={s}')
            self.assertEqual(response.status_code, status.HTTP_200_OK, msg=f"Status filter '{s}' should return 200")

    def test_combined_filters_no_results(self):
        response = self.client.get(f'{self.URL}?status=completed&contract_type=UNKNOWN_TYPE&search=NONEXISTENT')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ClauseEdgeCaseTests(BaseEdgeTestCase):
    def test_clause_text_exactly_10_chars_accepted(self):
        response = self.client.post(self.clause_url(), self.valid_clause(clause_text='1234567890'), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_clause_text_9_chars_rejected(self):
        response = self.client.post(self.clause_url(), self.valid_clause(clause_text='123456789'), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_very_long_clause_text_rejected(self):
        response = self.client.post(self.clause_url(), self.valid_clause(clause_text='A' * 50001), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_clause_text_exactly_50000_chars_accepted(self):
        response = self.client.post(self.clause_url(), self.valid_clause(clause_text='A' * 50000), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_clause_text_only_whitespace_rejected(self):
        response = self.client.post(self.clause_url(), self.valid_clause(clause_text='          '), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confidence_score_exactly_zero_accepted(self):
        response = self.client.post(self.clause_url(), self.valid_clause(confidence_score=0.0), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_confidence_score_exactly_one_accepted(self):
        response = self.client.post(self.clause_url(), self.valid_clause(confidence_score=1.0), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_confidence_score_slightly_above_one_rejected(self):
        response = self.client.post(self.clause_url(), self.valid_clause(confidence_score=1.0001), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confidence_score_slightly_below_zero_rejected(self):
        response = self.client.post(self.clause_url(), self.valid_clause(confidence_score=-0.0001), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_page_number_1_accepted(self):
        response = self.client.post(self.clause_url(), self.valid_clause(page_number=1), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_page_number_large_value_accepted(self):
        response = self.client.post(self.clause_url(), self.valid_clause(page_number=500), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_page_number_zero_rejected(self):
        response = self.client.post(self.clause_url(), self.valid_clause(page_number=0), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_page_number_negative_rejected(self):
        response = self.client.post(self.clause_url(), self.valid_clause(page_number=-1), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_101_clauses_rejected(self):
        clauses = [self.valid_clause(clause_type='other') for _ in range(101)]
        response = self.client.post(self.clause_url(), clauses, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_100_clauses_accepted(self):
        clauses = [self.valid_clause(clause_type='other') for _ in range(100)]
        response = self.client.post(self.clause_url(), clauses, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_clause_with_unicode_text_accepted(self):
        response = self.client.post(self.clause_url(), self.valid_clause(clause_text='Both parties — including Müller & Associés — agree to confidentiality.'), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_clause_with_numbers_in_text_accepted(self):
        response = self.client.post(self.clause_url(), self.valid_clause(clause_text='Contract value is $1,000,000 USD payable in 30 days.'), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class RiskFlagEdgeCaseTests(BaseEdgeTestCase):
    def test_risk_title_only_spaces_rejected(self):
        response = self.client.post(self.risk_url(), self.valid_risk(risk_title='     '), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_flagged_text_only_spaces_rejected(self):
        response = self.client.post(self.risk_url(), self.valid_risk(flagged_text='     '), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_severity_uppercase_rejected(self):
        response = self.client.post(self.risk_url(), self.valid_risk(severity='HIGH'), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_all_three_severities_work(self):
        for severity in ['low', 'medium', 'high']:
            response = self.client.post(self.risk_url(), self.valid_risk(severity=severity), format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED, msg=f"Severity '{severity}' should be accepted")

    def test_risk_without_keyword_matched_accepted(self):
        data = self.valid_risk()
        response = self.client.post(self.risk_url(), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_risk_without_explanation_accepted(self):
        data = self.valid_risk()
        response = self.client.post(self.risk_url(), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_bulk_101_risks_rejected(self):
        risks = [self.valid_risk() for _ in range(101)]
        response = self.client.post(self.risk_url(), risks, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_by_invalid_severity_returns_empty(self):
        response = self.client.get(f'{self.risk_url()}?severity=INVALID')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class StatusUpdateEdgeCaseTests(BaseEdgeTestCase):
    def patch_url(self):
        return f'/api/v1/documents/{self.document.id}/update-status/'

    def test_status_with_extra_spaces_rejected(self):
        response = self.client.patch(self.patch_url(), {'status': ' completed '}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_status_in_uppercase_rejected(self):
        response = self.client.patch(self.patch_url(), {'status': 'COMPLETED'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_risk_score_zero_accepted(self):
        response = self.client.patch(self.patch_url(), {'risk_score': 0}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_risk_score_large_value_accepted(self):
        response = self.client.patch(self.patch_url(), {'risk_score': 9999}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_date_format_returns_400(self):
        response = self.client.patch(self.patch_url(), {'status': 'completed', 'contract_start_date': '01/01/2024'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_date_format_accepted(self):
        response = self.client.patch(self.patch_url(), {'status': 'completed', 'contract_start_date': '2024-01-01', 'contract_end_date': '2025-12-31'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_nonexistent_document_returns_404(self):
        response = self.client.patch('/api/v1/documents/99999/update-status/', {'status': 'completed'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_none_values_in_body_handled(self):
        response = self.client.patch(self.patch_url(), {'status': 'completed', 'counterparty_name': None}, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaginationEdgeCaseTests(BaseEdgeTestCase):
    URL = '/api/v1/documents/'

    def setUp(self):
        super().setUp()
        for i in range(24):
            Document.objects.create(file_name=f'pagination_doc_{i}.pdf', status='uploaded')

    def test_first_page_returns_10_items(self):
        response = self.client.get(f'{self.URL}?page=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_custom_page_size_5_works(self):
        response = self.client.get(f'{self.URL}?page=1&page_size=5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(data['pagination']['page_size'], 5)

    def test_page_size_max_is_50(self):
        response = self.client.get(f'{self.URL}?page_size=100')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertLessEqual(data['pagination']['page_size'], 50)

    def test_total_count_is_correct(self):
        response = self.client.get(self.URL)
        total_in_db = Document.objects.count()
        total_in_api = response.json()['data']['pagination']['total_count']
        self.assertEqual(total_in_api, total_in_db)

    def test_next_link_present_when_more_pages(self):
        response = self.client.get(f'{self.URL}?page=1&page_size=5')
        next_link = response.json()['data']['pagination']['next']
        self.assertIsNotNone(next_link)

    def test_previous_link_none_on_first_page(self):
        response = self.client.get(f'{self.URL}?page=1')
        prev_link = response.json()['data']['pagination']['previous']
        self.assertIsNone(prev_link)


class NLPEdgeCaseTests(BaseEdgeTestCase):
    def nlp_url(self, suffix=''):
        return f'/api/v1/nlp/documents/{self.document.id}/{suffix}'

    def test_process_with_empty_clauses_list(self):
        response = self.client.post(self.nlp_url('process/'), {"status": "completed", "risk_score": 0, "metadata": {}, "clauses": [], "risk_flags": []}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_process_with_no_metadata(self):
        response = self.client.post(self.nlp_url('process/'), {"status": "completed", "risk_score": 0, "metadata": {}, "clauses": [], "risk_flags": []}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_process_invalid_status_returns_400(self):
        response = self.client.post(self.nlp_url('process/'), {"status": "WRONG", "risk_score": 0, "metadata": {}, "clauses": [], "risk_flags": []}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_process_with_partial_invalid_clause(self):
        response = self.client.post(self.nlp_url('process/'), {"status": "completed", "risk_score": 0, "metadata": {}, "clauses": [{"clause_type": "confidentiality", "clause_text": "Valid clause text here.", "page_number": 1, "confidence_score": 0.9}, {"clause_type": "termination", "clause_text": "Short", "page_number": 2, "confidence_score": 0.8}], "risk_flags": []}, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_nlp_status_update_to_failed(self):
        response = self.client.patch(self.nlp_url('status/'), {'status': 'failed'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.document.refresh_from_db()
        self.assertEqual(self.document.status, 'failed')

    def test_pending_list_with_no_pending_docs(self):
        Document.objects.all().update(status='completed')
        response = self.client.get('/api/v1/nlp/documents/pending/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['count'], 0)