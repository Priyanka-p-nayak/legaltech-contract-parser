"""
pagination.py
=============
Custom pagination classes used across all list endpoints.

Two sizes exist because document lists and clause/risk-flag
lists have very different realistic sizes per page — see the
WHY comment on each class below for the reasoning.
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


# ============================================================
# STANDARD PAGINATION CLASS
# Used in document list API to return data page by page.
#
# Usage in URL:
#   GET /api/v1/documents/?page=1
#   GET /api/v1/documents/?page=2&page_size=5
# ============================================================

class StandardPagination(PageNumberPagination):
    """
    Standard pagination for all list endpoints.

    Default: 10 items per page
    Maximum: 50 items per page
    Query param for page size: page_size

    WHY 10/50 instead of Django's default 100: a document list
    row carries a fair amount of nested info (counts, dates,
    risk score). 10 per page keeps each response small and fast
    for dashboard rendering, while still letting a power user
    bump it to 50 via ?page_size= when they want more at once.
    """

    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50
    page_query_param = 'page'

    def get_paginated_response(self, data):
        """Override to return our standard response format."""
        return Response({
            "success":    True,
            "message":    f"{self.page.paginator.count} document(s) found.",
            "status_code": 200,
            "data": {
                "pagination": {
                    "total_count":   self.page.paginator.count,
                    "total_pages":   self.page.paginator.num_pages,
                    "current_page":  self.page.number,
                    "page_size":     self.get_page_size(self.request),
                    "next":          self.get_next_link(),
                    "previous":      self.get_previous_link(),
                },
                "documents": data,
            }
        })


# ============================================================
# SMALL PAGINATION CLASS
# For endpoints that return smaller lists
# e.g. clauses and risk flags for one document
# ============================================================

class SmallPagination(PageNumberPagination):
    """
    Smaller pagination for clause and risk flag lists.
    Default: 20 items per page
    Maximum: 100 items per page
    """
    page_size              = 20
    page_size_query_param  = 'page_size'
    max_page_size          = 100
    page_query_param       = 'page'