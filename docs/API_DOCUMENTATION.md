# LegalTech API Documentation

**Version:** 1.0.0  
**Base URL:** `http://127.0.0.1:8000/api/v1/`  
**Built by:** Member 1 — Django Backend  
**Last Updated:** July 2, 2026

>  Back to [Project README](../README.md) ·
> 🗄️ See [Database Models Deep Dive](DATABASE_MODELS.md) ·
> 🖥️ See [Member 3 Dashboard Guide](MEMBER3_GUIDE.md) ·
> 🐳 See [Docker Guide](DOCKER_GUIDE.md)
---

## 📑 Table of Contents

- [Quick Reference Table](#-quick-reference-table)
- [Response Format](#-response-format)
- [Error Codes](#-error-codes)
- [Utility Endpoints](#-utility-endpoints)
- [Document Endpoints](#-document-endpoints)
- [Clause Endpoints](#-clause-endpoints)
- [Risk Flag Endpoints](#-risk-flag-endpoints)
- [Dashboard Endpoint](#-dashboard-endpoint)
- [NLP Integration Endpoints](#-nlp-integration-endpoints)
- [Common Workflows](#-common-workflows)
- [Performance Notes](#-performance-notes)
- [Testing](#-testing)

---

## ⚡ Quick Reference Table

| # | Method | Endpoint | Purpose |
|---|---|---|---|
| 1 | GET | `/health/` | Check API is running |
| 2 | GET | `/stats/` | System-wide statistics |
| 3 | GET | `/dashboard/` | All dashboard data in one call |
| 4 | POST | `/documents/upload/` | Upload a PDF contract |
| 5 | GET | `/documents/` | List documents (paginated, filterable) |
| 6 | GET | `/documents/{id}/` | Full document detail with nested data |
| 7 | GET | `/documents/{id}/summary/` | Risk/clause summary for cards |
| 8 | PATCH | `/documents/{id}/update-status/` | Update status and metadata |
| 9 | POST | `/documents/{id}/clauses/` | Save extracted clause(s) |
| 10 | GET | `/documents/{id}/clauses/` | Get all clauses for a document |
| 11 | POST | `/documents/{id}/risks/` | Save risk flag(s) |
| 12 | GET | `/documents/{id}/risks/` | Get all risk flags for a document |
| 13 | GET | `/nlp/documents/pending/` | List documents awaiting NLP |
| 14 | GET | `/nlp/documents/{id}/` | Fetch document for NLP processing |
| 15 | POST | `/nlp/documents/{id}/process/` | Submit complete NLP results |
| 16 | PATCH | `/nlp/documents/{id}/status/` | Update processing status only |
| 17 | GET | `/nlp/documents/{id}/results/` | Get NLP results grouped by type |

---

## 📦 Response Format

Every single API response — success or error — follows this exact shape:

```json
{
    "success": true,
    "message": "Human readable message",
    "status_code": 200,
    "data": { }
}