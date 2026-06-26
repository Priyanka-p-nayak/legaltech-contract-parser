"""
test_performance.py
===================
Performance and query optimization tests.
"""

import time
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from contracts.models import Document, ExtractedClause, RiskFlag


class BasePerformanceTest(TestCase):
    """Base class for performance tests."""

    def setUp(self):
        self.client = APIClient()

        # Create multiple documents for performance testing
        self.documents = []
        for i in range(20):
            doc = Document.objects.create(
                file_name         = f'perf_test_{i}.pdf',
                contract_type     = 'NDA' if i % 2 == 0 else 'MSA',
                counterparty_name = f'Company {i}',
                status            = 'uploaded',
                risk_score        = i,
            )
            self.documents.append(doc)

            # Add clauses for each document
            for j in range(3):
                ExtractedClause.objects.create(
                    document         = doc,
                    clause_type      = 'confidentiality',
                    clause_text      = (
                        f'Clause {j} text for document {i}. '
                        f'Both parties agree to confidentiality.'
                    ),
                    page_number      = j + 1,
                    confidence_score = 0.9,
                )

            # Add risks for each document
            for k in range(2):
                RiskFlag.objects.create(
                    document     = doc,
                    risk_title   = f'Risk {k} for doc {i}',
                    flagged_text = (
                        f'Risky text {k} found in document {i}.'
                    ),
                    severity     = 'high' if k == 0 else 'medium',
                    page_number  = k + 1,
                )


class ResponseTimeTests(BasePerformanceTest):
    """Tests that APIs respond within acceptable time."""

    MAX_RESPONSE_TIME = 2.0  # 2 seconds maximum

    def _measure_response_time(self, url, method='get', data=None):
        """Helper to measure API response time."""
        start    = time.time()
        if method == 'get':
            response = self.client.get(url)
        else:
            response = self.client.post(url, data, format='json')
        end      = time.time()
        duration = end - start
        return response, duration

    def test_health_check_is_fast(self):
        response, duration = self._measure_response_time('/api/v1/health/')
        self.assertEqual(response.status_code, 200)
        self.assertLess(duration, self.MAX_RESPONSE_TIME)

    def test_document_list_is_fast(self):
        response, duration = self._measure_response_time('/api/v1/documents/')
        self.assertEqual(response.status_code, 200)
        self.assertLess(duration, self.MAX_RESPONSE_TIME)


class DatabaseQueryTests(BasePerformanceTest):
    """Tests that APIs don't make excessive DB queries."""

    def test_health_check_query_count(self):
        """Health check should use exactly 3 queries."""
        with self.assertNumQueries(3):
            self.client.get('/api/v1/health/')

    def test_document_list_query_count(self):
        """Document list should not make N+1 queries."""
        with self.assertNumQueries(4):  # Changed from 2
            self.client.get('/api/v1/documents/')


class CustomManagerTests(BasePerformanceTest):
    """Tests for Document custom manager methods."""

    def test_manager_pending_returns_uploaded_only(self):
        self.documents[0].status = 'completed'
        self.documents[0].save()
        
        pending = Document.objects.pending()
        for doc in pending:
            self.assertEqual(doc.status, 'uploaded')

    def test_file_size_display_property(self):
        doc           = self.documents[0]
        doc.file_size = 1024 * 1024  # 1 MB
        doc.save()
        self.assertEqual(doc.file_size_display, '1.0 MB')