"""
test_integration.py
===================
Integration tests that test the complete flow
from upload → NLP processing → results retrieval.

Run with:
    python manage.py test integration.test_integration
"""

import json
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

from contracts.models import Document, ExtractedClause, RiskFlag


class FullIntegrationTest(TestCase):
    """
    Tests the complete lifecycle of a document:
    Upload → NLP Processing → Verify Results
    """

    def setUp(self):
        self.client = APIClient()

    def _upload_document(self):
        """Helper: Upload a test PDF document."""
        pdf_file = SimpleUploadedFile(
            name         = 'integration_test.pdf',
            content      = b'%PDF-1.4 integration test content',
            content_type = 'application/pdf'
        )
        response = self.client.post(
            '/api/v1/documents/upload/',
            {
                'file':              pdf_file,
                'contract_type':     'NDA',
                'counterparty_name': 'Integration Test Corp',
            },
            format='multipart'
        )
        return response

    def test_complete_document_lifecycle(self):
        """
        Test complete flow:
        1. Upload document
        2. Check it appears in pending list
        3. Mark as processing
        4. Submit NLP results
        5. Verify all data saved
        6. Check document is completed
        """

        # Step 1: Upload document
        upload_response = self._upload_document()
        self.assertEqual(upload_response.status_code, status.HTTP_201_CREATED)

        document_id = upload_response.json()['data']['id']

        # Step 2: Check pending list
        pending_response = self.client.get('/api/v1/nlp/documents/pending/')
        self.assertEqual(pending_response.status_code, status.HTTP_200_OK)

        pending_ids = [d['id'] for d in pending_response.json()['data']['documents']]
        self.assertIn(document_id, pending_ids)

        # Step 3: Mark as processing
        status_response = self.client.patch(
            f'/api/v1/nlp/documents/{document_id}/status/',
            {'status': 'processing'},
            format='json'
        )
        self.assertEqual(status_response.status_code, status.HTTP_200_OK)

        doc = Document.objects.get(id=document_id)
        self.assertEqual(doc.status, 'processing')

        # Step 4: Submit NLP results
        nlp_payload = {
            "status": "completed",
            "risk_score": 2,
            "metadata": {
                "counterparty_name": "Integration Test Corp",
                "governing_law": "California, USA",
                "contract_start_date": "2024-01-01",
                "contract_end_date": "2025-12-31",
            },
            "clauses": [
                {
                    "clause_type": "confidentiality",
                    "clause_text": "Both parties agree to maintain strict confidentiality of all shared information.",
                    "page_number": 2,
                    "confidence_score": 0.95,
                },
                {
                    "clause_type": "termination",
                    "clause_text": "Either party may terminate this agreement with 30 days written notice to the other.",
                    "page_number": 5,
                    "confidence_score": 0.88,
                },
            ],
            "risk_flags": [
                {
                    "risk_title": "Unlimited Liability Found",
                    "flagged_text": "The vendor shall be liable for unlimited damages from any breach whatsoever.",
                    "keyword_matched": "unlimited liability",
                    "severity": "high",
                    "page_number": 4,
                    "explanation": "Unlimited liability creates uncapped risk.",
                },
                {
                    "risk_title": "Exclusive Rights Clause",
                    "flagged_text": "Client retains exclusive rights to all work products and deliverables created.",
                    "keyword_matched": "exclusive",
                    "severity": "medium",
                    "page_number": 6,
                },
            ],
        }

        process_response = self.client.post(
            f'/api/v1/nlp/documents/{document_id}/process/',
            nlp_payload,
            format='json'
        )
        self.assertEqual(process_response.status_code, status.HTTP_201_CREATED)

        # Step 5: Verify in database
        doc = Document.objects.get(id=document_id)
        self.assertEqual(doc.status, 'completed')
        self.assertEqual(doc.risk_score, 2)

        clauses = ExtractedClause.objects.filter(document=doc)
        self.assertEqual(clauses.count(), 2)

        risks = RiskFlag.objects.filter(document=doc)
        self.assertEqual(risks.count(), 2)

        # Step 6: Get NLP results
        results_response = self.client.get(f'/api/v1/nlp/documents/{document_id}/results/')
        self.assertEqual(results_response.status_code, status.HTTP_200_OK)

    def test_cannot_reprocess_completed_document(self):
        """
        A completed document should not be processed again.
        Returns 409 Conflict (not 400) because this is a state conflict.
        """
        # Upload
        upload = self._upload_document()
        doc_id = upload.json()['data']['id']

        # Process once
        payload = {
            "status": "completed",
            "risk_score": 0,
            "metadata": {},
            "clauses": [],
            "risk_flags": [],
        }
        self.client.post(
            f'/api/v1/nlp/documents/{doc_id}/process/',
            payload,
            format='json'
        )

    # Try to process again — should return 409 Conflict
        response = self.client.post(
            f'/api/v1/nlp/documents/{doc_id}/process/',
            payload,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_409_CONFLICT,
            msg="Re-processing completed doc should return 409 Conflict"
        )

    def test_document_removed_from_pending_after_processing(self):
        """After processing, document should not be in pending list."""
        upload = self._upload_document()
        doc_id = upload.json()['data']['id']

        pending_before = self.client.get('/api/v1/nlp/documents/pending/')
        ids_before = [d['id'] for d in pending_before.json()['data']['documents']]
        self.assertIn(doc_id, ids_before)

        self.client.post(
            f'/api/v1/nlp/documents/{doc_id}/process/',
            {"status": "completed", "risk_score": 0, "metadata": {}, "clauses": [], "risk_flags": []},
            format='json'
        )

        pending_after = self.client.get('/api/v1/nlp/documents/pending/')
        ids_after = [d['id'] for d in pending_after.json()['data']['documents']]
        self.assertNotIn(doc_id, ids_after)

    def test_stats_update_after_processing(self):
        """Stats endpoint should reflect updated counts."""
        stats_before = self.client.get('/api/v1/stats/')
        before_data = stats_before.json()['data']

        upload = self._upload_document()
        doc_id = upload.json()['data']['id']

        self.client.post(
            f'/api/v1/nlp/documents/{doc_id}/process/',
            {
                "status": "completed",
                "risk_score": 1,
                "metadata": {},
                "clauses": [{"clause_type": "other", "clause_text": "Test clause text here for stats.", "page_number": 1, "confidence_score": 0.9}],
                "risk_flags": [{"risk_title": "Test Risk", "flagged_text": "Some risky text found here.", "severity": "low", "page_number": 1}],
            },
            format='json'
        )

        stats_after = self.client.get('/api/v1/stats/')
        after_data = stats_after.json()['data']

        self.assertEqual(after_data['total_documents'], before_data['total_documents'] + 1)
        self.assertGreater(after_data['total_clauses'], before_data['total_clauses'])

    def test_document_summary_after_processing(self):
        """Summary should show correct risk counts after processing."""
        upload = self._upload_document()
        doc_id = upload.json()['data']['id']

        self.client.post(
            f'/api/v1/nlp/documents/{doc_id}/process/',
            {
                "status": "completed",
                "risk_score": 3,
                "metadata": {},
                "clauses": [],
                "risk_flags": [
                    {"risk_title": "High Risk 1", "flagged_text": "Unlimited liability clause here.", "severity": "high", "page_number": 1},
                    {"risk_title": "High Risk 2", "flagged_text": "Indemnify all parties without limit.", "severity": "high", "page_number": 2},
                    {"risk_title": "Medium Risk 1", "flagged_text": "Exclusive rights to all deliverables.", "severity": "medium", "page_number": 3},
                ],
            },
            format='json'
        )

        summary_response = self.client.get(f'/api/v1/documents/{doc_id}/summary/')
        self.assertEqual(summary_response.status_code, status.HTTP_200_OK)

        summary = summary_response.json()['data']
        self.assertEqual(summary['risk_summary']['total'], 3)
        self.assertEqual(summary['risk_summary']['high'], 2)
        self.assertEqual(summary['risk_summary']['medium'], 1)