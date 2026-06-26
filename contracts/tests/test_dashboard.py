"""
test_dashboard.py
=================
Tests for the dashboard-facing API endpoints.
Verifies all data Member 3's dashboard needs
is returned correctly.
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile

from contracts.models import Document, ExtractedClause, RiskFlag


class BaseDashboardTest(TestCase):
    """Base class for dashboard tests."""

    def setUp(self):
        self.client = APIClient()

        # Create test documents with different statuses
        self.doc1 = Document.objects.create(
            file_name         = 'contract_nda.pdf',
            contract_type     = 'NDA',
            counterparty_name = 'Acme Corporation',
            governing_law     = 'California, USA',
            status            = 'completed',
            risk_score        = 3,
            file_size         = 1024 * 512,
        )

        self.doc2 = Document.objects.create(
            file_name         = 'contract_msa.pdf',
            contract_type     = 'MSA',
            counterparty_name = 'Tech Solutions Ltd',
            governing_law     = 'New York, USA',
            status            = 'uploaded',
            risk_score        = 0,
            file_size         = 1024 * 256,
        )

        self.doc3 = Document.objects.create(
            file_name         = 'contract_emp.pdf',
            contract_type     = 'Employment',
            counterparty_name = 'StartupXYZ',
            governing_law     = 'Delaware, USA',
            status            = 'processing',
            risk_score        = 1,
            file_size         = 1024 * 128,
        )

        # Add clauses to doc1
        ExtractedClause.objects.create(
            document         = self.doc1,
            clause_type      = 'confidentiality',
            clause_text      = (
                'Both parties agree to maintain strict '
                'confidentiality of all shared information.'
            ),
            page_number      = 2,
            confidence_score = 0.95,
        )
        ExtractedClause.objects.create(
            document         = self.doc1,
            clause_type      = 'termination',
            clause_text      = (
                'Either party may terminate this agreement '
                'with 30 days written notice.'
            ),
            page_number      = 5,
            confidence_score = 0.88,
        )

        # Add risk flags to doc1
        self.high_risk = RiskFlag.objects.create(
            document        = self.doc1,
            risk_title      = 'Unlimited Liability Found',
            flagged_text    = (
                'The vendor shall be liable for unlimited damages.'
            ),
            keyword_matched = 'unlimited liability',
            severity        = 'high',
            page_number     = 4,
            is_resolved     = False,
        )
        self.medium_risk = RiskFlag.objects.create(
            document        = self.doc1,
            risk_title      = 'Exclusive Rights Clause',
            flagged_text    = (
                'Client retains exclusive rights to all work products.'
            ),
            keyword_matched = 'exclusive',
            severity        = 'medium',
            page_number     = 6,
            is_resolved     = False,
        )
        self.resolved_risk = RiskFlag.objects.create(
            document        = self.doc1,
            risk_title      = 'Minor Concern Resolved',
            flagged_text    = (
                'Some minor language concern found here.'
            ),
            severity        = 'low',
            page_number     = 8,
            is_resolved     = True,
        )


# ============================================================
# TEST GROUP 1: DASHBOARD OVERVIEW ENDPOINT
# GET /api/v1/dashboard/
# ============================================================

class DashboardOverviewTests(BaseDashboardTest):
    """Tests for GET /api/v1/dashboard/"""

    URL = '/api/v1/dashboard/'

    def test_returns_200(self):
        """Dashboard should return 200 OK."""
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

    # ── Summary Tests ──────────────────────────────────────

    def test_has_summary_section(self):
        """Response should have summary section."""
        response = self.client.get(self.URL)
        self.assertIn('summary', response.json()['data'])

    def test_summary_has_total_documents(self):
        """Summary should include total_documents."""
        response = self.client.get(self.URL)
        self.assertIn(
            'total_documents',
            response.json()['data']['summary']
        )

    def test_summary_total_documents_is_correct(self):
        """total_documents should match DB count."""
        response = self.client.get(self.URL)
        self.assertEqual(
            response.json()['data']['summary']['total_documents'],
            Document.objects.count()
        )

    def test_summary_has_total_clauses(self):
        """Summary should include total_clauses."""
        response = self.client.get(self.URL)
        self.assertIn(
            'total_clauses',
            response.json()['data']['summary']
        )

    def test_summary_has_total_risks(self):
        """Summary should include total_risks."""
        response = self.client.get(self.URL)
        self.assertIn(
            'total_risks',
            response.json()['data']['summary']
        )

    def test_summary_has_total_resolved(self):
        """Summary should include total_resolved."""
        response = self.client.get(self.URL)
        self.assertIn(
            'total_resolved',
            response.json()['data']['summary']
        )

    def test_summary_has_total_unresolved(self):
        """Summary should include total_unresolved."""
        response = self.client.get(self.URL)
        self.assertIn(
            'total_unresolved',
            response.json()['data']['summary']
        )

    def test_summary_resolved_count_is_correct(self):
        """total_resolved count should match DB."""
        response = self.client.get(self.URL)
        self.assertEqual(
            response.json()['data']['summary']['total_resolved'],
            RiskFlag.objects.filter(is_resolved=True).count()
        )

    def test_summary_unresolved_count_is_correct(self):
        """total_unresolved count should match DB."""
        response = self.client.get(self.URL)
        self.assertEqual(
            response.json()['data']['summary']['total_unresolved'],
            RiskFlag.objects.filter(is_resolved=False).count()
        )

    # ── Status Breakdown Tests ─────────────────────────────

    def test_has_status_breakdown(self):
        """Response should have status_breakdown."""
        response = self.client.get(self.URL)
        self.assertIn(
            'status_breakdown',
            response.json()['data']
        )

    def test_status_breakdown_has_all_statuses(self):
        """status_breakdown should have all 4 statuses."""
        response   = self.client.get(self.URL)
        breakdown  = response.json()['data']['status_breakdown']
        self.assertIn('uploaded',   breakdown)
        self.assertIn('processing', breakdown)
        self.assertIn('completed',  breakdown)
        self.assertIn('failed',     breakdown)

    def test_status_breakdown_counts_correct(self):
        """Status counts should match DB."""
        response  = self.client.get(self.URL)
        breakdown = response.json()['data']['status_breakdown']
        self.assertEqual(
            breakdown['uploaded'],
            Document.objects.filter(status='uploaded').count()
        )
        self.assertEqual(
            breakdown['completed'],
            Document.objects.filter(status='completed').count()
        )

    # ── Risk Breakdown Tests ───────────────────────────────

    def test_has_risk_breakdown(self):
        """Response should have risk_breakdown."""
        response = self.client.get(self.URL)
        self.assertIn('risk_breakdown', response.json()['data'])

    def test_risk_breakdown_has_all_severities(self):
        """risk_breakdown should have high/medium/low."""
        response  = self.client.get(self.URL)
        breakdown = response.json()['data']['risk_breakdown']
        self.assertIn('high',   breakdown)
        self.assertIn('medium', breakdown)
        self.assertIn('low',    breakdown)

    def test_risk_breakdown_counts_correct(self):
        """Risk counts should match DB."""
        response  = self.client.get(self.URL)
        breakdown = response.json()['data']['risk_breakdown']
        self.assertEqual(
            breakdown['high'],
            RiskFlag.objects.filter(severity='high').count()
        )
        self.assertEqual(
            breakdown['medium'],
            RiskFlag.objects.filter(severity='medium').count()
        )

    # ── Recent Documents Tests ─────────────────────────────

    def test_has_recent_documents(self):
        """Response should have recent_documents list."""
        response = self.client.get(self.URL)
        self.assertIn(
            'recent_documents',
            response.json()['data']
        )

    def test_recent_documents_is_list(self):
        """recent_documents should be a list."""
        response = self.client.get(self.URL)
        self.assertIsInstance(
            response.json()['data']['recent_documents'],
            list
        )

    def test_recent_documents_max_5(self):
        """recent_documents should return at most 5."""
        # Create 10 more documents
        for i in range(10):
            Document.objects.create(
                file_name=f'extra_{i}.pdf',
                status='uploaded'
            )
        response = self.client.get(self.URL)
        self.assertLessEqual(
            len(response.json()['data']['recent_documents']),
            5
        )

    def test_recent_document_has_required_fields(self):
        """Each recent document should have required fields."""
        response = self.client.get(self.URL)
        docs     = response.json()['data']['recent_documents']

        if docs:
            doc = docs[0]
            required_fields = [
                'id',
                'file_name',
                'contract_type',
                'counterparty_name',
                'status',
                'risk_score',
                'uploaded_at',
                'total_clauses',
                'total_risks',
            ]
            for field in required_fields:
                self.assertIn(
                    field,
                    doc,
                    msg=f"recent_documents missing field: {field}"
                )

    def test_recent_document_total_clauses_correct(self):
        """total_clauses in recent doc should be correct."""
        response = self.client.get(self.URL)
        docs     = response.json()['data']['recent_documents']

        # Find doc1 in recent docs
        doc1_data = next(
            (d for d in docs if d['id'] == self.doc1.id),
            None
        )

        if doc1_data:
            expected = ExtractedClause.objects.filter(
                document=self.doc1
            ).count()
            self.assertEqual(
                doc1_data['total_clauses'],
                expected
            )

    # ── Recent High Risks Tests ────────────────────────────

    def test_has_recent_high_risks(self):
        """Response should have recent_high_risks list."""
        response = self.client.get(self.URL)
        self.assertIn(
            'recent_high_risks',
            response.json()['data']
        )

    def test_recent_high_risks_only_high_severity(self):
        """recent_high_risks should only contain high severity."""
        response = self.client.get(self.URL)
        risks    = response.json()['data']['recent_high_risks']

        for risk in risks:
            self.assertEqual(
                risk['severity'],
                'high',
                msg="recent_high_risks should only contain high severity"
            )

    def test_recent_high_risks_only_unresolved(self):
        """recent_high_risks should only contain unresolved."""
        response = self.client.get(self.URL)
        risks    = response.json()['data']['recent_high_risks']

        for risk in risks:
            self.assertFalse(
                risk['is_resolved'],
                msg="recent_high_risks should only contain unresolved"
            )

    def test_recent_high_risk_has_required_fields(self):
        """Each risk in recent_high_risks should have fields."""
        response = self.client.get(self.URL)
        risks    = response.json()['data']['recent_high_risks']

        if risks:
            risk = risks[0]
            required_fields = [
                'id',
                'risk_title',
                'severity',
                'document_id',
                'document_name',
                'page_number',
                'is_resolved',
                'flagged_at',
            ]
            for field in required_fields:
                self.assertIn(
                    field,
                    risk,
                    msg=f"recent_high_risks missing field: {field}"
                )

    # ── Contract Type Breakdown Tests ──────────────────────

    def test_has_contract_type_breakdown(self):
        """Response should have contract_type_breakdown."""
        response = self.client.get(self.URL)
        self.assertIn(
            'contract_type_breakdown',
            response.json()['data']
        )

    def test_contract_type_breakdown_is_list(self):
        """contract_type_breakdown should be a list."""
        response = self.client.get(self.URL)
        self.assertIsInstance(
            response.json()['data']['contract_type_breakdown'],
            list
        )


# ============================================================
# TEST GROUP 2: CORS TESTS
# ============================================================

class CORSTests(BaseDashboardTest):
    """Tests for CORS configuration."""

    def test_cors_headers_present_on_api_response(self):
        """
        CORS headers should be present when Origin is sent.
        Member 3's browser will send Origin header.
        """
        response = self.client.get(
            '/api/v1/dashboard/',
            HTTP_ORIGIN='http://localhost:3000'
        )
        self.assertEqual(response.status_code, 200)

    def test_options_request_allowed(self):
        """
        OPTIONS preflight request should be allowed.
        Browsers send this before POST requests.
        """
        response = self.client.options(
            '/api/v1/documents/upload/',
            HTTP_ORIGIN='http://localhost:3000',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
        )
        # Should not return 403 Forbidden
        self.assertNotEqual(response.status_code, 403)

    def test_health_check_accessible_from_different_origin(self):
        """
        Health check should work from any origin.
        """
        response = self.client.get(
            '/api/v1/health/',
            HTTP_ORIGIN='http://localhost:5173'
        )
        self.assertEqual(response.status_code, 200)


# ============================================================
# TEST GROUP 3: DOCUMENT LIST FOR DASHBOARD
# ============================================================

class DocumentListDashboardTests(BaseDashboardTest):
    """
    Tests for document list endpoint as used by dashboard.
    Member 3 will use this to show all contracts.
    """

    URL = '/api/v1/documents/'

    def test_list_returns_200(self):
        """List should return 200."""
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, 200)

    def test_list_has_pagination(self):
        """List should have pagination info."""
        response = self.client.get(self.URL)
        self.assertIn('pagination', response.json()['data'])

    def test_list_documents_have_required_fields(self):
        """
        Each document in list should have fields
        that dashboard needs to display.
        """
        response = self.client.get(self.URL)
        data     = response.json()['data']

        # Get first document from paginated response
        docs = data.get('documents', [])

        if docs:
            doc = docs[0]
            dashboard_required_fields = [
                'id',
                'file_name',
                'contract_type',
                'counterparty_name',
                'status',
                'risk_score',
                'uploaded_at',
                'total_clauses',
                'total_risks',
            ]
            for field in dashboard_required_fields:
                self.assertIn(
                    field,
                    doc,
                    msg=f"Document list missing field for dashboard: {field}"
                )

    def test_filter_completed_for_dashboard(self):
        """
        Dashboard will filter completed documents.
        """
        response = self.client.get(
            f'{self.URL}?status=completed'
        )
        self.assertEqual(response.status_code, 200)

    def test_search_for_dashboard(self):
        """
        Dashboard search functionality should work.
        """
        response = self.client.get(
            f'{self.URL}?search=Acme'
        )
        self.assertEqual(response.status_code, 200)


# ============================================================
# TEST GROUP 4: DOCUMENT DETAIL FOR DASHBOARD
# ============================================================

class DocumentDetailDashboardTests(BaseDashboardTest):
    """
    Tests for document detail endpoint as used by dashboard.
    Member 3 shows full contract analysis on detail page.
    """

    def test_detail_has_all_dashboard_fields(self):
        """
        Detail should have all fields dashboard needs.
        """
        response = self.client.get(
            f'/api/v1/documents/{self.doc1.id}/'
        )
        data = response.json()['data']

        dashboard_fields = [
            'id',
            'file_name',
            'contract_type',
            'counterparty_name',
            'governing_law',
            'contract_start_date',
            'contract_end_date',
            'status',
            'risk_score',
            'total_clauses',
            'total_risks',
            'clauses',
            'risk_flags',
            'uploaded_at',
        ]

        for field in dashboard_fields:
            self.assertIn(
                field,
                data,
                msg=f"Document detail missing field: {field}"
            )

    def test_nested_clauses_have_dashboard_fields(self):
        """
        Nested clauses should have fields dashboard needs.
        """
        response = self.client.get(
            f'/api/v1/documents/{self.doc1.id}/'
        )
        clauses = response.json()['data']['clauses']

        if clauses:
            clause = clauses[0]
            required = [
                'id',
                'clause_type',
                'clause_text',
                'page_number',
                'confidence_score',
            ]
            for field in required:
                self.assertIn(
                    field,
                    clause,
                    msg=f"Clause missing dashboard field: {field}"
                )

    def test_nested_risks_have_dashboard_fields(self):
        """
        Nested risk flags should have fields dashboard needs.
        """
        response = self.client.get(
            f'/api/v1/documents/{self.doc1.id}/'
        )
        risks = response.json()['data']['risk_flags']

        if risks:
            risk = risks[0]
            required = [
                'id',
                'risk_title',
                'flagged_text',
                'severity',
                'page_number',
                'is_resolved',
                'keyword_matched',
            ]
            for field in required:
                self.assertIn(
                    field,
                    risk,
                    msg=f"Risk flag missing dashboard field: {field}"
                )


# ============================================================
# TEST GROUP 5: SUMMARY FOR DASHBOARD CARDS
# ============================================================

class SummaryDashboardTests(BaseDashboardTest):
    """
    Tests for summary endpoint.
    Member 3 uses this for individual document cards.
    """

    def test_summary_has_risk_summary(self):
        """Summary should have risk counts for dashboard."""
        response = self.client.get(
            f'/api/v1/documents/{self.doc1.id}/summary/'
        )
        data = response.json()['data']
        self.assertIn('risk_summary', data)

    def test_risk_summary_counts_match_db(self):
        """
        Risk summary high/medium/low counts
        should match actual DB counts.
        """
        response = self.client.get(
            f'/api/v1/documents/{self.doc1.id}/summary/'
        )
        risk_summary = response.json()['data']['risk_summary']

        self.assertEqual(
            risk_summary['high'],
            RiskFlag.objects.filter(
                document=self.doc1,
                severity='high'
            ).count()
        )
        self.assertEqual(
            risk_summary['medium'],
            RiskFlag.objects.filter(
                document=self.doc1,
                severity='medium'
            ).count()
        )

    def test_clause_summary_breakdown_correct(self):
        """
        Clause breakdown by type should be correct.
        """
        response = self.client.get(
            f'/api/v1/documents/{self.doc1.id}/summary/'
        )
        clause_summary = response.json()['data']['clause_summary']

        self.assertIn('confidentiality', clause_summary['breakdown'])
        self.assertIn('termination',     clause_summary['breakdown'])