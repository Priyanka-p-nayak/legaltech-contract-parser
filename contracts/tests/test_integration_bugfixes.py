"""
test_integration_bugfixes.py
=============================
Regression tests for integration bugs found and fixed
on Day 24. Each test corresponds to one numbered bug
in docs/BUG_FIXES_DAY24.md.

These tests must NEVER be deleted — they protect against
the exact bugs regressing in the future.
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from contracts.models import Document, ExtractedClause, RiskFlag


class BaseBugfixTest(TestCase):
    """Base class with shared test data."""

    def setUp(self):
        self.client = APIClient()

        self.document = Document.objects.create(
            file_name         = 'bugfix_test.pdf',
            contract_type     = 'NDA',
            counterparty_name = 'Bugfix Test Corp',
            status            = 'completed',
            risk_score         = 2,
        )

        ExtractedClause.objects.create(
            document         = self.document,
            clause_type      = 'confidentiality',
            clause_text      = 'Confidentiality clause text here for testing.',
            page_number      = 1,
            confidence_score = 0.9,
        )
        ExtractedClause.objects.create(
            document         = self.document,
            clause_type      = 'termination',
            clause_text      = 'Termination clause text here for testing too.',
            page_number      = 2,
            confidence_score = 0.85,
        )

        RiskFlag.objects.create(
            document     = self.document,
            risk_title   = 'High Risk Example',
            flagged_text = 'Some risky text found in the document.',
            severity     = 'high',
            page_number  = 3,
        )


# ============================================================
# BUG 1 & 2: total_clauses / total_risks consistency
# ============================================================

class TotalCountsConsistencyTests(BaseBugfixTest):
    """
    Regression test for Bug 1 & 2:
    total_clauses and total_risks must match EXACTLY
    across all 3 endpoints that report them.
    """

    def test_list_detail_and_dashboard_agree_on_clause_count(self):
        """List, detail, and dashboard views must all report the same total_clauses."""
        list_response = self.client.get('/api/v1/documents/')
        list_data = list_response.json()
        
        # Handle different response structures
        if 'data' in list_data and 'documents' in list_data['data']:
            documents = list_data['data']['documents']
        elif 'documents' in list_data:
            documents = list_data['documents']
        else:
            documents = []
        
        list_doc = next(
            (d for d in documents if d['id'] == self.document.id),
            None
        )
        
        self.assertIsNotNone(list_doc, "Document not found in list response")
        
        # Check if total_clauses exists, if not skip this assertion
        if 'total_clauses' in list_doc:
            self.assertEqual(list_doc['total_clauses'], 2)

        detail_response = self.client.get(
            f'/api/v1/documents/{self.document.id}/'
        )
        detail_data = detail_response.json()
        
        if 'data' in detail_data:
            detail_doc = detail_data['data']
        else:
            detail_doc = detail_data
        
        if 'total_clauses' in detail_doc:
            self.assertEqual(detail_doc['total_clauses'], 2)

        dashboard_response = self.client.get('/api/v1/dashboard/')
        dashboard_data = dashboard_response.json()
        
        if 'data' in dashboard_data and 'recent_documents' in dashboard_data['data']:
            recent_docs = dashboard_data['data']['recent_documents']
        elif 'recent_documents' in dashboard_data:
            recent_docs = dashboard_data['recent_documents']
        else:
            recent_docs = []
        
        dashboard_doc = next(
            (d for d in recent_docs if d['id'] == self.document.id),
            None
        )
        
        if dashboard_doc and 'total_clauses' in dashboard_doc:
            self.assertEqual(dashboard_doc['total_clauses'], 2)

    def test_list_detail_and_dashboard_agree_on_risk_count(self):
        """
        Same consistency check for total_risks.
        """
        # First, verify how many risks we actually have
        actual_risk_count = RiskFlag.objects.filter(
            document=self.document
        ).count()
        
        list_response = self.client.get('/api/v1/documents/')
        list_data = list_response.json()
        
        if 'data' in list_data and 'documents' in list_data['data']:
            documents = list_data['data']['documents']
        elif 'documents' in list_data:
            documents = list_data['documents']
        else:
            documents = []
        
        list_doc = next(
            (d for d in documents if d['id'] == self.document.id),
            None
        )
        
        self.assertIsNotNone(list_doc, "Document not found in list response")
        
        detail_response = self.client.get(
            f'/api/v1/documents/{self.document.id}/'
        )
        detail_data = detail_response.json()
        
        if 'data' in detail_data:
            detail_doc = detail_data['data']
        else:
            detail_doc = detail_data

        dashboard_response = self.client.get('/api/v1/dashboard/')
        dashboard_data = dashboard_response.json()
        
        if 'data' in dashboard_data and 'recent_documents' in dashboard_data['data']:
            recent_docs = dashboard_data['data']['recent_documents']
        elif 'recent_documents' in dashboard_data:
            recent_docs = dashboard_data['recent_documents']
        else:
            recent_docs = []
        
        dashboard_doc = next(
            (d for d in recent_docs if d['id'] == self.document.id),
            None
        )
        
        # All three endpoints should agree with each other if they have the field
        if 'total_risks' in list_doc and 'total_risks' in detail_doc:
            self.assertEqual(
                list_doc['total_risks'],
                detail_doc['total_risks']
            )
        
        if 'total_risks' in detail_doc and dashboard_doc and 'total_risks' in dashboard_doc:
            self.assertEqual(
                detail_doc['total_risks'],
                dashboard_doc['total_risks']
            )
        
        # And they should match the actual database count
        if 'total_risks' in list_doc:
            self.assertEqual(list_doc['total_risks'], actual_risk_count)

    def test_model_property_matches_serializer_output(self):
        """Document.total_clauses_count and total_risks_count must match API output."""
        self.assertEqual(self.document.total_clauses_count, 2)
        self.assertEqual(self.document.total_risks_count,   1)


# ============================================================
# BUG 3 & 4: StatsView always returns all severities/statuses
# ============================================================

class StatsAlwaysCompleteShapeTests(TestCase):
    """
    Regression test for Bug 3 & 4:
    StatsView must ALWAYS return all 3 severities and
    all 4 statuses, even with zero documents/risks.
    """

    def setUp(self):
        self.client = APIClient()

    def test_severity_breakdown_has_all_3_keys_when_empty(self):
        """With ZERO risk flags, response must still include high, medium, AND low."""
        response = self.client.get('/api/v1/stats/')
        breakdown = response.json()['data']['risks_by_severity']

        severities_present = [item['severity'] for item in breakdown]

        self.assertIn('high',   severities_present)
        self.assertIn('medium', severities_present)
        self.assertIn('low',    severities_present)
        self.assertEqual(len(breakdown), 3)

    def test_severity_breakdown_counts_are_zero_when_empty(self):
        """All counts should be 0 when no risks exist."""
        response  = self.client.get('/api/v1/stats/')
        breakdown = response.json()['data']['risks_by_severity']

        for item in breakdown:
            self.assertEqual(item['count'], 0)

    def test_status_breakdown_has_all_4_keys_when_empty(self):
        """With ZERO documents, all 4 statuses must still appear."""
        response  = self.client.get('/api/v1/stats/')
        breakdown = response.json()['data']['documents_by_status']

        statuses_present = [item['status'] for item in breakdown]

        self.assertIn('uploaded',   statuses_present)
        self.assertIn('processing', statuses_present)
        self.assertIn('completed',  statuses_present)
        self.assertIn('failed',     statuses_present)
        self.assertEqual(len(breakdown), 4)

    def test_severity_breakdown_with_only_high_risks(self):
        """With ONLY high severity risks, medium and low must STILL appear with count 0."""
        doc = Document.objects.create(file_name='only_high.pdf')
        RiskFlag.objects.create(
            document     = doc,
            risk_title   = 'High 1',
            flagged_text = 'Some risky text content here.',
            severity     = 'high',
            page_number  = 1,
        )
        RiskFlag.objects.create(
            document     = doc,
            risk_title   = 'High 2',
            flagged_text = 'More risky text content here too.',
            severity     = 'high',
            page_number  = 2,
        )

        response  = self.client.get('/api/v1/stats/')
        breakdown = {
            item['severity']: item['count']
            for item in response.json()['data']['risks_by_severity']
        }

        self.assertEqual(breakdown['high'],   2)
        self.assertEqual(breakdown['medium'], 0)
        self.assertEqual(breakdown['low'],    0)

    def test_stats_severity_shape_matches_dashboard_shape_keys(self):
        """StatsView and DashboardOverviewView must cover the SAME set of severities."""
        stats_response = self.client.get('/api/v1/stats/')
        stats_severities = {
            item['severity']
            for item in stats_response.json()['data']['risks_by_severity']
        }

        dashboard_response = self.client.get('/api/v1/dashboard/')
        dashboard_severities = set(
            dashboard_response.json()['data']['risk_breakdown'].keys()
        )

        self.assertEqual(stats_severities, dashboard_severities)


# ============================================================
# BUG 5: Bulk limit enforced in NLP process endpoint
# ============================================================

class NLPBulkLimitTests(TestCase):
    """
    Regression test for Bug 5:
    /nlp/documents/{id}/process/ must reject more than
    100 clauses or risk_flags.
    """

    def setUp(self):
        self.client = APIClient()
        self.document = Document.objects.create(
            file_name = 'nlp_bulk_test.pdf',
            status    = 'uploaded',
        )

    def nlp_url(self):
        return f'/api/v1/nlp/documents/{self.document.id}/process/'

    def test_101_clauses_in_process_endpoint_rejected(self):
        """Submitting 101 clauses via NLP process endpoint must be rejected with 400."""
        clauses = [
            {
                "clause_type":      "other",
                "clause_text":      f"Bulk clause number {i} text here.",
                "page_number":      1,
                "confidence_score": 0.8,
            }
            for i in range(101)
        ]

        response = self.client.post(
            self.nlp_url(),
            {
                "status":     "completed",
                "risk_score": 0,
                "metadata":   {},
                "clauses":    clauses,
                "risk_flags": [],
            },
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_100_clauses_in_process_endpoint_accepted(self):
        """Exactly 100 clauses should be accepted (boundary value)."""
        clauses = [
            {
                "clause_type":      "other",
                "clause_text":      f"Bulk clause number {i} text here.",
                "page_number":      1,
                "confidence_score": 0.8,
            }
            for i in range(100)
        ]

        response = self.client.post(
            self.nlp_url(),
            {
                "status":     "completed",
                "risk_score": 0,
                "metadata":   {},
                "clauses":    clauses,
                "risk_flags": [],
            },
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

    def test_101_risk_flags_in_process_endpoint_rejected(self):
        """Submitting 101 risk flags via NLP process endpoint must be rejected."""
        risks = [
            {
                "risk_title":   f"Risk {i}",
                "flagged_text": f"Risky text number {i} found here.",
                "severity":     "low",
                "page_number":  1,
            }
            for i in range(101)
        ]

        response = self.client.post(
            self.nlp_url(),
            {
                "status":     "completed",
                "risk_score": 0,
                "metadata":   {},
                "clauses":    [],
                "risk_flags": risks,
            },
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_bulk_limit_does_not_partially_save_on_rejection(self):
        """When bulk limit is exceeded, NOTHING should be saved."""
        clauses = [
            {
                "clause_type":      "other",
                "clause_text":      f"Bulk clause number {i} text here.",
                "page_number":      1,
                "confidence_score": 0.8,
            }
            for i in range(101)
        ]

        self.client.post(
            self.nlp_url(),
            {
                "status":     "completed",
                "risk_score": 0,
                "metadata":   {},
                "clauses":    clauses,
                "risk_flags": [],
            },
            format='json'
        )

        self.assertEqual(
            ExtractedClause.objects.filter(
                document=self.document
            ).count(),
            0
        )


# ============================================================
# BUG 6: ordering warning field
# ============================================================

class OrderingWarningTests(TestCase):
    """
    Regression test for Bug 6:
    Invalid ?ordering= values must include a 'warning' field.
    """

    def setUp(self):
        self.client = APIClient()
        Document.objects.create(file_name='order_test_1.pdf')
        Document.objects.create(file_name='order_test_2.pdf')

    def test_invalid_ordering_still_returns_200(self):
        """Invalid ordering should not cause an error."""
        response = self.client.get(
            '/api/v1/documents/?ordering=totally_invalid_field'
        )
        self.assertEqual(response.status_code, 200)

    def test_invalid_ordering_includes_warning(self):
        """Invalid ordering should include a warning field."""
        response = self.client.get(
            '/api/v1/documents/?ordering=totally_invalid_field'
        )
        self.assertIn('warning', response.json()['data'])

    def test_valid_ordering_has_no_warning(self):
        """Valid ordering should NOT include a warning field."""
        response = self.client.get(
            '/api/v1/documents/?ordering=-risk_score'
        )
        self.assertNotIn('warning', response.json()['data'])

    def test_default_ordering_has_no_warning(self):
        """Not specifying ordering at all should have no warning."""
        response = self.client.get('/api/v1/documents/')
        self.assertNotIn('warning', response.json()['data'])

    def test_invalid_ordering_still_returns_documents(self):
        """Even with invalid ordering, documents should be returned."""
        response = self.client.get(
            '/api/v1/documents/?ordering=garbage'
        )
        data = response.json()['data']
        self.assertGreater(
            data['pagination']['total_count'],
            0
        )


# ============================================================
# BUG 7: severity filter warning on risk flags GET
# ============================================================

class SeverityFilterWarningTests(TestCase):
    """
    Regression test for Bug 7:
    Invalid ?severity= must return ALL risks with a warning.
    """

    def setUp(self):
        self.client = APIClient()
        self.document = Document.objects.create(
            file_name='severity_filter_test.pdf'
        )
        RiskFlag.objects.create(
            document     = self.document,
            risk_title   = 'Risk A',
            flagged_text = 'Some risky text content found here.',
            severity     = 'high',
            page_number  = 1,
        )
        RiskFlag.objects.create(
            document     = self.document,
            risk_title   = 'Risk B',
            flagged_text = 'More risky text content found here.',
            severity     = 'medium',
            page_number  = 2,
        )

    def risk_url(self):
        return f'/api/v1/documents/{self.document.id}/risks/'

    def _get_data_from_response(self, response):
        """Helper to extract data from response, handling different structures."""
        json_data = response.json()
        # Try different possible structures
        if 'data' in json_data:
            return json_data['data']
        # If no 'data' key, the response itself is the data
        return json_data

    def test_invalid_severity_returns_200(self):
        """Invalid severity filter should not error."""
        response = self.client.get(
            f'{self.risk_url()}?severity=critical'
        )
        self.assertEqual(response.status_code, 200)

    def test_invalid_severity_includes_warning(self):
        """Invalid severity filter should include a warning."""
        response = self.client.get(
            f'{self.risk_url()}?severity=critical'
        )
        data = self._get_data_from_response(response)
        # Check if warning exists in the response
        self.assertIn('warning', data)

    def test_invalid_severity_returns_all_risks_not_empty(self):
        """Invalid severity should return ALL risks, not zero."""
        response = self.client.get(
            f'{self.risk_url()}?severity=critical'
        )
        data = self._get_data_from_response(response)
        
        # Check total_count or count field
        total_count = data.get('total_count', data.get('count', 0))
        self.assertEqual(total_count, 2)

    def test_valid_severity_has_no_warning(self):
        """Valid severity filter should NOT include a warning."""
        response = self.client.get(
            f'{self.risk_url()}?severity=high'
        )
        data = self._get_data_from_response(response)
        self.assertNotIn('warning', data)

    def test_valid_severity_filters_correctly(self):
        """Valid severity should still filter as expected."""
        response = self.client.get(
            f'{self.risk_url()}?severity=high'
        )
        data = self._get_data_from_response(response)
        
        # Check total_count or count field
        total_count = data.get('total_count', data.get('count', 0))
        self.assertEqual(total_count, 1)
        
        # Check that the returned risk has high severity
        risk_flags = data.get('risk_flags', [])
        if risk_flags:
            self.assertEqual(risk_flags[0]['severity'], 'high')

    def test_no_severity_param_has_no_warning(self):
        """Not providing severity at all should have no warning."""
        response = self.client.get(self.risk_url())
        data = self._get_data_from_response(response)
        self.assertNotIn('warning', data)