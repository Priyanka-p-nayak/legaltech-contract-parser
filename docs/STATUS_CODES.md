# LegalTech API — HTTP Status Code Reference

## Status Code Summary

| Code | Name | When Used |
|---|---|---|
| 200 | OK | Successful GET and PATCH requests |
| 201 | Created | Successful POST (new resource created) |
| 207 | Multi-Status | Partial bulk success |
| 400 | Bad Request | Invalid data, missing fields, validation failed |
| 404 | Not Found | Resource with given ID does not exist |
| 409 | Conflict | Resource already in conflicting state |
| 413 | Payload Too Large | File exceeds 10MB |
| 500 | Internal Server Error | Unexpected server error |

---

## Endpoint Status Code Map

### Utility
| Endpoint | Method | Success | Error Cases |
|---|---|---|---|
| `/health/` | GET | 200 | - |
| `/stats/` | GET | 200 | - |

### Documents
| Endpoint | Method | Success | Error Cases |
|---|---|---|---|
| `/documents/upload/` | POST | 201 | 400 (no file, wrong type, empty file), 413 (too large) |
| `/documents/` | GET | 200 | 400 (invalid status filter) |
| `/documents/{id}/` | GET | 200 | 404 (not found) |
| `/documents/{id}/summary/` | GET | 200 | 404 (not found) |
| `/documents/{id}/update-status/` | PATCH | 200 | 400 (invalid data, empty body), 404 (not found) |
| `/documents/{id}/clauses/` | POST | 201 | 400 (validation failed, empty list), 404 (doc not found) |
| `/documents/{id}/clauses/` | GET | 200 | 404 (doc not found) |
| `/documents/{id}/risks/` | POST | 201 | 400 (validation failed, empty list), 404 (doc not found) |
| `/documents/{id}/risks/` | GET | 200 | 404 (doc not found) |

### NLP Integration
| Endpoint | Method | Success | Error Cases |
|---|---|---|---|
| `/nlp/documents/pending/` | GET | 200 | - |
| `/nlp/documents/{id}/` | GET | 200 | 404 (not found) |
| `/nlp/documents/{id}/process/` | POST | 201 | 400 (invalid data), 404 (not found), 409 (already processed) |
| `/nlp/documents/{id}/status/` | PATCH | 200 | 400 (invalid status), 404 (not found) |
| `/nlp/documents/{id}/results/` | GET | 200 | 404 (not found) |

---

## Error Codes Reference

| Error Code | HTTP Status | Description |
|---|---|---|
| `NO_FILE_PROVIDED` | 400 | No file in upload request |
| `INVALID_FILE_TYPE` | 400 | File is not a .pdf |
| `EMPTY_FILE` | 400 | File is 0 bytes |
| `FILE_TOO_LARGE` | 413 | File exceeds 10MB |
| `INVALID_STATUS` | 400 | Status value not in allowed list |
| `INVALID_SEVERITY` | 400 | Severity not low/medium/high |
| `EMPTY_REQUEST_BODY` | 400 | Request body is empty |
| `BULK_LIMIT_EXCEEDED` | 400 | More than 100 items in bulk request |
| `DOCUMENT_NOT_FOUND` | 404 | Document ID does not exist |
| `DOCUMENT_ALREADY_PROCESSED` | 409 | Cannot re-process completed document |
| `INVALID_DATE_FORMAT` | 400 | Date not in YYYY-MM-DD format |
| `VALIDATION_ERROR` | 400 | Field-level validation failed |
| `DATABASE_ERROR` | 500 | Unexpected database failure |
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected server error |

---

## Standard Response Format

### Success:
```json
{
    "success": true,
    "message": "Document retrieved successfully.",
    "status_code": 200,
    "data": { }
}