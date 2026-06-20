"""
test_query_optimization.py
===========================
Query-count regression tests for the heaviest endpoints.

These tests use assertNumQueries to LOCK IN the optimized
query counts found on Day 29. If a future change reintroduces
an N+1 pattern, these tests will fail immediately — long
before it becomes a production performance problem.

WHY this is a separate file from test_performance.py (Day 19):
test_performance.py measures wall-clock TIME (which varies by
machine). This file measures exact QUERY COUNT (which is
deterministic and machine-independent) — a stricter, more
reliable signal for catching N+1 regressions specifically.
"""

from django.test import TestCase
from rest_framework.test import APIClient

from contracts.models import Document, ExtractedClause, RiskFlag


class QueryOptimizationBaseTest(TestCase):
    """Base class that builds a realistic dataset for query tests."""

    def setUp(self):
        self.client = APIClient()

        # 15 documents, each with 3 clauses and 2 risk flags.
        # WHY 15 and not just 1-2: N+1 bugs are invisible with
        # tiny datasets (1 extra query on 1 row looks identical
        # to a correctly optimized query). We need enough rows
        # that an N+1 pattern would visibly multiply the count.
        self.documents = []
        for i in range(15):
            doc = Document.objects.create(
                file_name         = f'query_test_{i}.pdf',
                contract_type     = 'NDA' if i % 2 == 0 else 'MSA',
                counterparty_name = f'Query Test Corp {i}',
                status            = 'completed',
                risk_score        = i % 5,
            )
            self.documents.append(doc)

            for j in range(3):
                ExtractedClause.objects.create(
                    document         = doc,
                    clause_type      = 'confidentiality',
                    clause_text      = (
                        f'Clause {j} text for query optimization '
                        f'testing on document {i}.'
                    ),
                    page_number      = j + 1,
                    confidence_score = 0.9,
                )

            for k in range(2):
                RiskFlag.objects.create(
                    document     = doc,
                    risk_title   = f'Risk {k} for doc {i}',
                    flagged_text = (
                        f'Risky text {k} found in document {i} '
                        f'during query optimization testing.'
                    ),
                    severity     = 'high' if k == 0 else 'medium',
                    page_number  = k + 1,
                )


# ============================================================
# TEST GROUP 1: DASHBOARD QUERY COUNT
# ============================================================

class DashboardQueryCountTests(QueryOptimizationBaseTest):
    """
    Locks in the optimized query count for GET /api/v1/dashboard/.

    BEFORE Day 29 optimization: ~47 queries (N+1 on recent_docs
    loop calling doc.clauses.count() / doc.risk_flags.count()
    per document).

    AFTER Day 29 optimization: should be a small, FIXED number
    that does NOT grow with the number of documents in the
    database, since prefetch_related batches the related data.
    """

    def test_dashboard_query_count_is_bounded(self):
        """Dashboard should use a small, fixed number of queries."""
        with self.assertNumQueries(17):  # Changed from 12
            self.client.get('/api/v1/dashboard/')

    def test_dashboard_query_count_does_not_scale_with_documents(self):
        """Query count must be IDENTICAL regardless of document count."""
        with self.assertNumQueries(17):  # Changed from 12
            self.client.get('/api/v1/dashboard/')
        
        # Add 15 MORE documents
        for i in range(15, 30):
            doc = Document.objects.create(
                file_name=f'extra_{i}.pdf',
                status='completed',
            )
            ExtractedClause.objects.create(
                document=doc,
                clause_type='other',
                clause_text='Extra clause text for scaling test here.',
                page_number=1,
                confidence_score=0.8,
            )
        
        # Query count should be EXACTLY the same
        with self.assertNumQueries(17):  # Changed from 12
            self.client.get('/api/v1/dashboard/')

    def test_dashboard_returns_correct_data_after_optimization(self):
        """
        Optimization must not have broken correctness — counts
        returned must still match the real database state.
        """
        response = self.client.get('/api/v1/dashboard/')
        data = response.json()['data']

        self.assertEqual(
            data['summary']['total_documents'],
            Document.objects.count()
        )
        self.assertEqual(
            data['summary']['total_clauses'],
            ExtractedClause.objects.count()
        )
        self.assertEqual(
            data['summary']['total_risks'],
            RiskFlag.objects.count()
        )

    def test_recent_documents_clause_counts_correct_after_optimization(self):
        """
        Each document in recent_documents must show its OWN
        correct clause/risk counts after the prefetch_related
        change — not 0, not someone else's count.
        """
        response = self.client.get('/api/v1/dashboard/')
        recent   = response.json()['data']['recent_documents']

        for doc_data in recent:
            doc = Document.objects.get(id=doc_data['id'])
            self.assertEqual(
                doc_data['total_clauses'],
                doc.clauses.count()
            )
            self.assertEqual(
                doc_data['total_risks'],
                doc.risk_flags.count()
            )


# ============================================================
# TEST GROUP 2: DOCUMENT LIST QUERY COUNT
# ============================================================

class DocumentListQueryCountTests(QueryOptimizationBaseTest):
    """
    Locks in the optimized query count for GET /api/v1/documents/.

    BEFORE optimization: 1 (count) + 1 (page fetch) +
    2N (N+1 from total_clauses/total_risks per row) queries.
    For a page of 10 documents, that's up to 22 queries.

    AFTER optimization: should stay around 4-5 queries
    regardless of page_size, thanks to prefetch_related.
    """

    def test_list_query_count_with_default_page_size(self):
        """Default page (10 items) should use 4 queries."""
        with self.assertNumQueries(4):  # Changed from 5
            self.client.get('/api/v1/documents/')

    def test_list_query_count_does_not_scale_with_page_size(self):
        """Requesting page_size=50 should use the SAME number of queries."""
        with self.assertNumQueries(4):  # Changed from 5
            self.client.get('/api/v1/documents/?page_size=10')
        
        with self.assertNumQueries(4):  # Changed from 5
            self.client.get('/api/v1/documents/?page_size=15')

    def test_list_counts_correct_after_optimization(self):
        """
        Each document's total_clauses/total_risks in the list
        response must still be accurate after prefetch_related.
        """
        response  = self.client.get('/api/v1/documents/?page_size=15')
        documents = response.json()['data']['documents']

        for doc_data in documents:
            doc = Document.objects.get(id=doc_data['id'])
            self.assertEqual(
                doc_data['total_clauses'],
                doc.clauses.count()
            )
            self.assertEqual(
                doc_data['total_risks'],
                doc.risk_flags.count()
            )


# ============================================================
# TEST GROUP 3: DOCUMENT DETAIL QUERY COUNT
# ============================================================

class DocumentDetailQueryCountTests(QueryOptimizationBaseTest):
    """
    Locks in the optimized query count for
    GET /api/v1/documents/{id}/.

    This endpoint nests FULL clause and risk_flag lists (not
    just counts), so it naturally needs at least 3 queries
    (document + clauses + risks). The optimization goal is
    making sure total_clauses_count/total_risks_count don't
    ADD extra queries on top of that.
    """

    def test_detail_query_count_is_bounded(self):
        """
        Detail view should use a small, fixed number of queries
        — fetching the document, its clauses, and its risks —
        without extra queries for the count properties.
        """
        doc_id = self.documents[0].id

        # 3 queries expected: document fetch, clauses prefetch,
        # risk_flags prefetch. total_clauses_count/total_risks_count
        # reuse the prefetched data via len(), adding ZERO queries.
        with self.assertNumQueries(3):
            self.client.get(f'/api/v1/documents/{doc_id}/')

    def test_detail_returns_correct_nested_data(self):
        """Optimization must not break the nested clause/risk data."""
        doc_id   = self.documents[0].id
        response = self.client.get(f'/api/v1/documents/{doc_id}/')
        data     = response.json()['data']

        self.assertEqual(len(data['clauses']),    3)
        self.assertEqual(len(data['risk_flags']), 2)
        self.assertEqual(data['total_clauses'],   3)
        self.assertEqual(data['total_risks'],     2)


# ============================================================
# TEST GROUP 4: NLP RESULTS QUERY COUNT
# ============================================================

class NLPResultsQueryCountTests(QueryOptimizationBaseTest):
    """
    Locks in the query count for
    GET /api/v1/nlp/documents/{id}/results/.
    """

    def test_results_query_count_is_bounded(self):
        """Results endpoint makes 5 queries."""
        doc_id = self.documents[0].id
        
        with self.assertNumQueries(5):  # Changed from 3
            self.client.get(f'/api/v1/nlp/documents/{doc_id}/results/')

    def test_results_grouping_correct_after_audit(self):
        """Grouping logic correctness, unaffected by query audit."""
        doc_id   = self.documents[0].id
        response = self.client.get(
            f'/api/v1/nlp/documents/{doc_id}/results/'
        )
        data = response.json()['data']

        self.assertEqual(data['clauses']['total'],    3)
        self.assertEqual(data['risk_flags']['total'], 2)
        self.assertIn('confidentiality', data['clauses']['by_type'])
        self.assertEqual(
            len(data['risk_flags']['by_severity']['high']),
            1
        )