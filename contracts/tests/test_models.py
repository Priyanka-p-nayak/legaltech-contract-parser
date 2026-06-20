"""
test_models.py
==============
Unit tests for all Django models: Document, ExtractedClause, RiskFlag.
"""

from django.test import TestCase
from contracts.models import Document, ExtractedClause, RiskFlag


# ============================================================
# HELPERS
# ============================================================

def make_document(**kwargs):
    defaults = {
        'file_name': 'test_contract.pdf', 'contract_type': 'NDA',
        'counterparty_name': 'Test Company Ltd', 'governing_law': 'California, USA',
        'status': 'uploaded', 'risk_score': 0, 'file_size': 1024,
    }
    defaults.update(kwargs)
    return Document.objects.create(**defaults)

def make_clause(document, **kwargs):
    defaults = {
        'document': document, 'clause_type': 'confidentiality',
        'clause_text': 'Both parties agree to maintain strict confidentiality of all proprietary information shared.',
        'page_number': 1, 'confidence_score': 0.95,
    }
    defaults.update(kwargs)
    return ExtractedClause.objects.create(**defaults)

def make_risk(document, **kwargs):
    defaults = {
        'document': document, 'risk_title': 'Unlimited Liability Found',
        'flagged_text': 'The party agrees to unlimited liability for all damages caused.',
        'keyword_matched': 'unlimited liability', 'severity': 'high',
        'page_number': 2, 'explanation': 'Unlimited liability creates uncapped financial exposure.',
    }
    defaults.update(kwargs)
    return RiskFlag.objects.create(**defaults)


# ============================================================
# DOCUMENT MODEL TESTS
# ============================================================

class DocumentModelCreationTests(TestCase):
    def test_create_document_with_required_fields(self):
        doc = Document.objects.create(file_name='simple_contract.pdf')
        self.assertIsNotNone(doc.id)
        self.assertEqual(doc.file_name, 'simple_contract.pdf')

    def test_create_document_with_all_fields(self):
        doc = make_document()
        self.assertEqual(doc.file_name, 'test_contract.pdf')
        self.assertEqual(doc.contract_type, 'NDA')
        self.assertEqual(doc.status, 'uploaded')

    def test_document_count_increases(self):
        count_before = Document.objects.count()
        make_document()
        self.assertEqual(Document.objects.count(), count_before + 1)

class DocumentModelDefaultTests(TestCase):
    def setUp(self):
        self.doc = Document.objects.create(file_name='default_test.pdf')

    def test_default_status_is_uploaded(self):
        self.assertEqual(self.doc.status, 'uploaded')

    def test_default_risk_score_is_zero(self):
        self.assertEqual(self.doc.risk_score, 0)

    def test_uploaded_at_is_set_automatically(self):
        self.assertIsNotNone(self.doc.uploaded_at)

class DocumentModelStringTests(TestCase):
    def test_str_returns_filename_and_status(self):
        doc = make_document(file_name='contract.pdf', status='uploaded')
        self.assertEqual(str(doc), 'contract.pdf (uploaded)')

class DocumentModelOrderingTests(TestCase):
    def test_documents_ordered_newest_first(self):
        doc1 = make_document(file_name='first.pdf')
        doc2 = make_document(file_name='second.pdf')
        doc3 = make_document(file_name='third.pdf')
        documents = list(Document.objects.all())
        self.assertEqual(documents[0].id, doc3.id)
        self.assertEqual(documents[2].id, doc1.id)

class DocumentModelDeletionTests(TestCase):
    def test_document_can_be_deleted(self):
        doc = make_document()
        doc_id = doc.id
        doc.delete()
        self.assertFalse(Document.objects.filter(id=doc_id).exists())


# ============================================================
# EXTRACTED CLAUSE MODEL TESTS
# ============================================================

class ExtractedClauseModelCreationTests(TestCase):
    def setUp(self):
        self.document = make_document()

    def test_create_clause_with_all_fields(self):
        clause = make_clause(self.document)
        self.assertEqual(clause.clause_type, 'confidentiality')
        self.assertEqual(clause.confidence_score, 0.95)

    def test_clause_related_name_works(self):
        make_clause(self.document, clause_type='confidentiality')
        make_clause(self.document, clause_type='termination')
        self.assertEqual(self.document.clauses.count(), 2)

class ExtractedClauseModelCascadeTests(TestCase):
    def test_clauses_deleted_when_document_deleted(self):
        document = make_document()
        make_clause(document)
        make_clause(document)
        self.assertEqual(ExtractedClause.objects.filter(document=document).count(), 2)
        
        document.delete()
        self.assertEqual(ExtractedClause.objects.count(), 0)


# ============================================================
# RISK FLAG MODEL TESTS
# ============================================================

class RiskFlagModelCreationTests(TestCase):
    def setUp(self):
        self.document = make_document()

    def test_create_risk_with_all_fields(self):
        risk = make_risk(self.document)
        self.assertEqual(risk.severity, 'high')
        self.assertFalse(risk.is_resolved)

    def test_risk_related_name_works(self):
        make_risk(self.document, risk_title='Risk 1')
        make_risk(self.document, risk_title='Risk 2')
        self.assertEqual(self.document.risk_flags.count(), 2)

class RiskFlagModelStringTests(TestCase):
    def setUp(self):
        self.document = make_document(file_name='contract.pdf')

    def test_str_format_is_correct(self):
        risk = make_risk(self.document, risk_title='Unlimited Liability', severity='high')
        self.assertEqual(str(risk), '[HIGH] Unlimited Liability — contract.pdf')

class RiskFlagModelCascadeTests(TestCase):
    def test_risks_deleted_when_document_deleted(self):
        document = make_document()
        make_risk(document)
        make_risk(document)
        
        document.delete()
        self.assertEqual(RiskFlag.objects.count(), 0)


# ============================================================
# RELATIONSHIP TESTS
# ============================================================

class ModelRelationshipTests(TestCase):
    def setUp(self):
        self.document = make_document()
        self.clause = make_clause(self.document)
        self.risk = make_risk(self.document)

    def test_document_has_correct_counts(self):
        self.assertEqual(self.document.clauses.count(), 1)
        self.assertEqual(self.document.risk_flags.count(), 1)

    def test_delete_all_data_in_correct_order(self):
        doc_id = self.document.id
        self.document.delete()
        self.assertFalse(Document.objects.filter(id=doc_id).exists())
        self.assertEqual(ExtractedClause.objects.filter(document_id=doc_id).count(), 0)
        self.assertEqual(RiskFlag.objects.filter(document_id=doc_id).count(), 0)