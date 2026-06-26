"""
test_serializers.py
===================
Unit tests for all DRF Serializers.
"""

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from contracts.models import Document
from contracts.serializers import (
    ExtractedClauseSerializer,
    RiskFlagSerializer,
    DocumentUploadSerializer,
    DocumentStatusUpdateSerializer,
)

def make_document(**kwargs):
    defaults = {
        'file_name': 'serializer_test.pdf', 'contract_type': 'NDA',
        'status': 'uploaded', 'risk_score': 0, 'file_size': 2048,
    }
    defaults.update(kwargs)
    return Document.objects.create(**defaults)


class ExtractedClauseSerializerTests(TestCase):
    def setUp(self):
        self.document = make_document()

    def _valid_data(self, **kwargs):
        defaults = {
            'document': self.document.id, 'clause_type': 'confidentiality',
            'clause_text': 'Both parties agree to confidentiality of all information shared.',
            'page_number': 1, 'confidence_score': 0.95,
        }
        defaults.update(kwargs)
        return defaults

    def test_valid_data_is_valid(self):
        serializer = ExtractedClauseSerializer(data=self._valid_data())
        self.assertTrue(serializer.is_valid())

    def test_confidence_score_above_one_is_invalid(self):
        serializer = ExtractedClauseSerializer(data=self._valid_data(confidence_score=1.5))
        self.assertFalse(serializer.is_valid())

    def test_page_number_zero_is_invalid(self):
        serializer = ExtractedClauseSerializer(data=self._valid_data(page_number=0))
        self.assertFalse(serializer.is_valid())

    def test_short_clause_text_is_invalid(self):
        serializer = ExtractedClauseSerializer(data=self._valid_data(clause_text='Short'))
        self.assertFalse(serializer.is_valid())


class RiskFlagSerializerTests(TestCase):
    def setUp(self):
        self.document = make_document()

    def _valid_data(self, **kwargs):
        defaults = {
            'document': self.document.id, 'risk_title': 'Unlimited Liability Found',
            'flagged_text': 'The party agrees to unlimited liability for damages.',
            'severity': 'high', 'page_number': 2,
        }
        defaults.update(kwargs)
        return defaults

    def test_valid_data_is_valid(self):
        serializer = RiskFlagSerializer(data=self._valid_data())
        self.assertTrue(serializer.is_valid())

    def test_invalid_severity_is_invalid(self):
        serializer = RiskFlagSerializer(data=self._valid_data(severity='critical'))
        self.assertFalse(serializer.is_valid())

    def test_empty_risk_title_is_invalid(self):
        serializer = RiskFlagSerializer(data=self._valid_data(risk_title='   '))
        self.assertFalse(serializer.is_valid())


class DocumentStatusUpdateSerializerTests(TestCase):
    def setUp(self):
        self.document = make_document()

    def test_valid_status_update(self):
        serializer = DocumentStatusUpdateSerializer(self.document, data={'status': 'completed'}, partial=True)
        self.assertTrue(serializer.is_valid())

    def test_invalid_status_fails(self):
        serializer = DocumentStatusUpdateSerializer(self.document, data={'status': 'INVALID'}, partial=True)
        self.assertFalse(serializer.is_valid())

    def test_negative_risk_score_fails(self):
        serializer = DocumentStatusUpdateSerializer(self.document, data={'risk_score': -1}, partial=True)
        self.assertFalse(serializer.is_valid())