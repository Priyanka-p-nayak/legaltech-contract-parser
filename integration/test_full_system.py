"""
test_full_system.py
====================
Full system integration tests.

Simulates the complete real-world workflow involving
all 3 team members' parts working together:

  Member 3 (Dashboard) → Member 1 (Backend) → Member 2 (NLP)
                              ↓
                    Member 1 (Backend) → Member 3 (Dashboard)

This is the highest-level test in the project —
it proves the WHOLE system works end to end.
"""

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

from contracts.models import Document, ExtractedClause, RiskFlag


class FullSystemWorkflowTest(TestCase):
    """
    Simulates the complete contract review workflow
    from upload to dashboard display.
    """

    def setUp(self):
        self.client = APIClient()

    def _make_pdf(self, name='full_system_test.pdf'):
        return SimpleUploadedFile(
            name         = name,
            content      = b'%PDF-1.4 full system test content',
            content_type = 'application/pdf'
        )

    # ────────────────────────────────────────────────────────
    # THE BIG TEST: Complete workflow simulation
    # ────────────────────────────────────────────────────────

    def test_complete_real_world_workflow(self):
        """
        SCENARIO:
        A paralegal uploads an NDA through the dashboard.
        The NLP module picks it up, processes it, and
        sends back clauses and risks. The dashboard then
        displays everything to senior counsel, who marks
        a risk as resolved.

        This single test walks through every stage.
        """

        # ══════════════════════════════════════════════════
        # STAGE 1: PARALEGAL UPLOADS PDF (via Member 3 dashboard)
        # ══════════════════════════════════════════════════
        upload_response = self.client.post(
            '/api/v1/documents/upload/',
            {
                'file':              self._make_pdf(),
                'contract_type':     'NDA',
                'counterparty_name': 'Globex Corporation',
            },
            format='multipart'
        )

        self.assertEqual(
            upload_response.status_code,
            status.HTTP_201_CREATED,
            msg="Stage 1 failed: PDF upload should succeed"
        )

        document_id = upload_response.json()['data']['id']
        self.assertEqual(
            upload_response.json()['data']['status'],
            'uploaded'
        )

        # ══════════════════════════════════════════════════
        # STAGE 2: DASHBOARD SHOWS NEW DOCUMENT (Member 3 reads)
        # ══════════════════════════════════════════════════
        dashboard_response = self.client.get('/api/v1/dashboard/')
        self.assertEqual(dashboard_response.status_code, 200)

        dashboard_data = dashboard_response.json()['data']
        recent_ids = [
            d['id'] for d in dashboard_data['recent_documents']
        ]
        self.assertIn(
            document_id,
            recent_ids,
            msg="Stage 2 failed: New doc should appear on dashboard"
        )

        # ══════════════════════════════════════════════════
        # STAGE 3: NLP MODULE FINDS PENDING WORK (Member 2 polls)
        # ══════════════════════════════════════════════════
        pending_response = self.client.get(
            '/api/v1/nlp/documents/pending/'
        )
        self.assertEqual(pending_response.status_code, 200)

        pending_ids = [
            d['id'] for d in pending_response.json()['data']['documents']
        ]
        self.assertIn(
            document_id,
            pending_ids,
            msg="Stage 3 failed: Doc should be pending NLP processing"
        )

        # ══════════════════════════════════════════════════
        # STAGE 4: NLP FETCHES DOCUMENT DETAILS (Member 2)
        # ══════════════════════════════════════════════════
        fetch_response = self.client.get(
            f'/api/v1/nlp/documents/{document_id}/'
        )
        self.assertEqual(fetch_response.status_code, 200)
        self.assertIn(
            'file_path',
            fetch_response.json()['data']
        )

        # ══════════════════════════════════════════════════
        # STAGE 5: NLP MARKS DOCUMENT AS PROCESSING (Member 2)
        # ══════════════════════════════════════════════════
        processing_response = self.client.patch(
            f'/api/v1/nlp/documents/{document_id}/status/',
            {'status': 'processing'},
            format='json'
        )
        self.assertEqual(processing_response.status_code, 200)

        doc = Document.objects.get(id=document_id)
        self.assertEqual(doc.status, 'processing')

        # ══════════════════════════════════════════════════
        # STAGE 6: DASHBOARD SHOWS "PROCESSING" STATUS
        # (Member 3 reads updated state)
        # ══════════════════════════════════════════════════
        detail_during_processing = self.client.get(
            f'/api/v1/documents/{document_id}/'
        )
        self.assertEqual(
            detail_during_processing.json()['data']['status'],
            'processing'
        )

        # ══════════════════════════════════════════════════
        # STAGE 7: NLP SUBMITS FULL RESULTS (Member 2's main call)
        # Simulates real spaCy/PyMuPDF output
        # ══════════════════════════════════════════════════
        nlp_results = {
            "status":     "completed",
            "risk_score": 3,
            "metadata": {
                "counterparty_name":   "Globex Corporation",
                "governing_law":       "Delaware, USA",
                "contract_start_date": "2024-02-01",
                "contract_end_date":   "2026-02-01",
            },
            "clauses": [
                {
                    "clause_type":      "confidentiality",
                    "clause_text": (
                        "Both parties agree to maintain strict "
                        "confidentiality of all proprietary "
                        "information shared during this agreement."
                    ),
                    "page_number":      2,
                    "confidence_score": 0.96,
                },
                {
                    "clause_type":      "termination",
                    "clause_text": (
                        "Either party may terminate this agreement "
                        "with 30 days written notice."
                    ),
                    "page_number":      5,
                    "confidence_score": 0.91,
                },
                {
                    "clause_type":      "indemnification",
                    "clause_text": (
                        "Each party shall indemnify and hold "
                        "harmless the other party from claims "
                        "arising out of breach of this agreement."
                    ),
                    "page_number":      6,
                    "confidence_score": 0.89,
                },
            ],
            "risk_flags": [
                {
                    "risk_title":      "Unlimited Liability Clause",
                    "flagged_text": (
                        "The vendor shall be liable for unlimited "
                        "damages arising from any breach whatsoever."
                    ),
                    "keyword_matched": "unlimited liability",
                    "severity":        "high",
                    "page_number":     4,
                    "explanation": (
                        "Unlimited liability clauses expose the "
                        "company to uncapped financial risk."
                    ),
                },
                {
                    "risk_title":      "Indemnification Risk",
                    "flagged_text": (
                        "Each party shall indemnify and hold "
                        "harmless the other from all claims."
                    ),
                    "keyword_matched": "indemnify",
                    "severity":        "high",
                    "page_number":     6,
                },
                {
                    "risk_title":      "Exclusive Rights Clause",
                    "flagged_text": (
                        "Client retains exclusive rights to all "
                        "work products created under this agreement."
                    ),
                    "keyword_matched": "exclusive",
                    "severity":        "medium",
                    "page_number":     7,
                },
            ],
        }

        process_response = self.client.post(
            f'/api/v1/nlp/documents/{document_id}/process/',
            nlp_results,
            format='json'
        )

        self.assertEqual(
            process_response.status_code,
            status.HTTP_201_CREATED,
            msg="Stage 7 failed: NLP results submission should succeed"
        )

        process_data = process_response.json()['data']
        self.assertEqual(process_data['total_clauses'], 3)
        self.assertEqual(process_data['total_risks'],   3)

        # ══════════════════════════════════════════════════
        # STAGE 8: VERIFY DATA SAVED CORRECTLY IN DATABASE
        # ══════════════════════════════════════════════════
        doc.refresh_from_db()
        self.assertEqual(doc.status,            'completed')
        self.assertEqual(doc.risk_score,         3)
        self.assertEqual(doc.governing_law,     'Delaware, USA')

        self.assertEqual(
            ExtractedClause.objects.filter(document=doc).count(),
            3
        )
        self.assertEqual(
            RiskFlag.objects.filter(document=doc).count(),
            3
        )

        # ══════════════════════════════════════════════════
        # STAGE 9: DASHBOARD NOW SHOWS COMPLETED DOCUMENT
        # (Member 3's main use case)
        # ══════════════════════════════════════════════════
        final_dashboard = self.client.get('/api/v1/dashboard/')
        dashboard_data   = final_dashboard.json()['data']

        self.assertGreaterEqual(
            dashboard_data['summary']['total_risks'],
            3
        )
        self.assertGreaterEqual(
            dashboard_data['risk_breakdown']['high'],
            2
        )

        # High risks should now appear in recent_high_risks
        high_risk_doc_ids = [
            r['document_id']
            for r in dashboard_data['recent_high_risks']
        ]
        self.assertIn(document_id, high_risk_doc_ids)

        # ══════════════════════════════════════════════════
        # STAGE 10: SENIOR COUNSEL OPENS FULL DOCUMENT DETAIL
        # (Member 3 detail page)
        # ══════════════════════════════════════════════════
        full_detail = self.client.get(
            f'/api/v1/documents/{document_id}/'
        )
        detail_data = full_detail.json()['data']

        self.assertEqual(detail_data['status'],        'completed')
        self.assertEqual(len(detail_data['clauses']),    3)
        self.assertEqual(len(detail_data['risk_flags']), 3)

        # Find the high-risk unlimited liability flag
        unlimited_liability_risk = next(
            (
                r for r in detail_data['risk_flags']
                if r['keyword_matched'] == 'unlimited liability'
            ),
            None
        )
        self.assertIsNotNone(unlimited_liability_risk)
        self.assertEqual(unlimited_liability_risk['severity'], 'high')
        self.assertFalse(unlimited_liability_risk['is_resolved'])

        # ══════════════════════════════════════════════════
        # STAGE 11: SENIOR COUNSEL MARKS RISK AS RESOLVED
        # (Member 3 → Member 1 API)
        # ══════════════════════════════════════════════════
        risk_id = unlimited_liability_risk['id']
        risk    = RiskFlag.objects.get(id=risk_id)
        risk.is_resolved = True
        risk.save()

        # ══════════════════════════════════════════════════
        # STAGE 12: DASHBOARD REFLECTS RESOLVED RISK COUNT
        # ══════════════════════════════════════════════════
        post_resolve_dashboard = self.client.get('/api/v1/dashboard/')
        post_resolve_data      = post_resolve_dashboard.json()['data']

        self.assertGreaterEqual(
            post_resolve_data['summary']['total_resolved'],
            1
        )

        # The resolved risk should NOT appear in recent_high_risks
        # (that list only shows unresolved high risks)
        resolved_risk_ids = [
            r['id'] for r in post_resolve_data['recent_high_risks']
        ]
        self.assertNotIn(risk_id, resolved_risk_ids)

        print("\n" + "=" * 60)
        print("  FULL SYSTEM WORKFLOW TEST: ALL 12 STAGES PASSED")
        print("=" * 60)

    # ────────────────────────────────────────────────────────
    # ADDITIONAL SYSTEM-LEVEL TESTS
    # ────────────────────────────────────────────────────────

    def test_multiple_documents_processed_independently(self):
        """
        SCENARIO:
        Two different documents are uploaded and processed
        at the same time. Their data must not mix.
        """

        # Upload two documents
        doc1_response = self.client.post(
            '/api/v1/documents/upload/',
            {
                'file':          self._make_pdf('doc1.pdf'),
                'contract_type': 'NDA',
            },
            format='multipart'
        )
        doc2_response = self.client.post(
            '/api/v1/documents/upload/',
            {
                'file':          self._make_pdf('doc2.pdf'),
                'contract_type': 'MSA',
            },
            format='multipart'
        )

        doc1_id = doc1_response.json()['data']['id']
        doc2_id = doc2_response.json()['data']['id']

        # Process doc1 with 2 clauses
        self.client.post(
            f'/api/v1/nlp/documents/{doc1_id}/process/',
            {
                "status":     "completed",
                "risk_score": 1,
                "metadata":   {},
                "clauses": [
                    {
                        "clause_type":      "confidentiality",
                        "clause_text":      "Doc1 confidentiality clause text.",
                        "page_number":      1,
                        "confidence_score": 0.9,
                    }
                ],
                "risk_flags": [
                    {
                        "risk_title":   "Doc1 Risk",
                        "flagged_text": "Doc1 risky text content found.",
                        "severity":     "high",
                        "page_number":  1,
                    }
                ],
            },
            format='json'
        )

        # Process doc2 with 3 clauses
        self.client.post(
            f'/api/v1/nlp/documents/{doc2_id}/process/',
            {
                "status":     "completed",
                "risk_score": 2,
                "metadata":   {},
                "clauses": [
                    {
                        "clause_type":      "termination",
                        "clause_text":      "Doc2 termination clause text.",
                        "page_number":      1,
                        "confidence_score": 0.8,
                    },
                    {
                        "clause_type":      "governing_law",
                        "clause_text":      "Doc2 governing law clause text.",
                        "page_number":      2,
                        "confidence_score": 0.85,
                    },
                ],
                "risk_flags": [],
            },
            format='json'
        )

        # Verify each document only has its own data
        doc1_clauses = ExtractedClause.objects.filter(
            document_id=doc1_id
        ).count()
        doc2_clauses = ExtractedClause.objects.filter(
            document_id=doc2_id
        ).count()

        self.assertEqual(doc1_clauses, 1)
        self.assertEqual(doc2_clauses, 2)

        doc1_risks = RiskFlag.objects.filter(
            document_id=doc1_id
        ).count()
        doc2_risks = RiskFlag.objects.filter(
            document_id=doc2_id
        ).count()

        self.assertEqual(doc1_risks, 1)
        self.assertEqual(doc2_risks, 0)

    def test_failed_document_does_not_appear_in_pending(self):
        """
        SCENARIO:
        NLP processing fails for a document.
        It should be marked 'failed' and removed from
        the pending queue, but still visible on dashboard.
        """
        upload = self.client.post(
            '/api/v1/documents/upload/',
            {'file': self._make_pdf('will_fail.pdf')},
            format='multipart'
        )
        doc_id = upload.json()['data']['id']

        # Mark as failed (simulating NLP module hitting an error)
        self.client.patch(
            f'/api/v1/nlp/documents/{doc_id}/status/',
            {'status': 'failed'},
            format='json'
        )

        # Should not be in pending list anymore
        pending = self.client.get(
            '/api/v1/nlp/documents/pending/'
        )
        pending_ids = [
            d['id'] for d in pending.json()['data']['documents']
        ]
        self.assertNotIn(doc_id, pending_ids)

        # Should still be visible in document list
        detail = self.client.get(f'/api/v1/documents/{doc_id}/')
        self.assertEqual(detail.json()['data']['status'], 'failed')

    def test_dashboard_stats_consistent_with_document_list(self):
        """
        SCENARIO:
        Numbers shown on dashboard summary must always match
        what's actually returned by the document list endpoint.
        """
        # Upload 3 documents
        for i in range(3):
            self.client.post(
                '/api/v1/documents/upload/',
                {'file': self._make_pdf(f'consistency_{i}.pdf')},
                format='multipart'
            )

        dashboard = self.client.get('/api/v1/dashboard/')
        doc_list  = self.client.get('/api/v1/documents/')

        dashboard_total = (
            dashboard.json()['data']['summary']['total_documents']
        )
        list_total = (
            doc_list.json()['data']['pagination']['total_count']
        )

        self.assertEqual(dashboard_total, list_total)

    def test_search_finds_uploaded_document_immediately(self):
        """
        SCENARIO:
        Right after upload, the document must be immediately
        searchable — no delay or caching issue.
        """
        self.client.post(
            '/api/v1/documents/upload/',
            {
                'file':              self._make_pdf('searchable.pdf'),
                'counterparty_name': 'UniqueSearchTestCorp',
            },
            format='multipart'
        )

        search_response = self.client.get(
            '/api/v1/documents/?search=UniqueSearchTestCorp'
        )

        documents = search_response.json()['data']['documents']
        self.assertEqual(len(documents), 1)
        self.assertEqual(
            documents[0]['counterparty_name'],
            'UniqueSearchTestCorp'
        )

    def test_bulk_upload_and_process_ten_documents(self):
        """
        SCENARIO:
        Simulates a paralegal uploading a batch of 10 contracts
        and the NLP module processing all of them.
        This matches the original project requirement:
        "Uploads a batch of 50 PDFs" (scaled down for test speed).
        """
        document_ids = []

        # Upload 10 documents
        for i in range(10):
            response = self.client.post(
                '/api/v1/documents/upload/',
                {
                    'file':          self._make_pdf(f'batch_{i}.pdf'),
                    'contract_type': 'NDA',
                },
                format='multipart'
            )
            document_ids.append(response.json()['data']['id'])

        # Verify all 10 are pending
        pending = self.client.get(
            '/api/v1/nlp/documents/pending/'
        )
        self.assertEqual(pending.json()['data']['count'], 10)

        # Process all 10
        for doc_id in document_ids:
            self.client.post(
                f'/api/v1/nlp/documents/{doc_id}/process/',
                {
                    "status":     "completed",
                    "risk_score": 1,
                    "metadata":   {},
                    "clauses": [
                        {
                            "clause_type":      "other",
                            "clause_text":      "Batch processed clause text here.",
                            "page_number":      1,
                            "confidence_score": 0.8,
                        }
                    ],
                    "risk_flags": [],
                },
                format='json'
            )

        # Verify none remain pending
        pending_after = self.client.get(
            '/api/v1/nlp/documents/pending/'
        )
        self.assertEqual(pending_after.json()['data']['count'], 0)

        # Verify all marked completed
        completed_count = Document.objects.filter(
            id__in=document_ids,
            status='completed'
        ).count()
        self.assertEqual(completed_count, 10)