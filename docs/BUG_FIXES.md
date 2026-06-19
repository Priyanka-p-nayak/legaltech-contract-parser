# Bug Fixes Log — LegalTech Backend

## Day 19 — June 25, 2026

### Bug Fix 1: Database Indexes Added
**Problem:** Filtering documents by status and ordering by uploaded_at was slow without database indexes.
**Fix:** Added `db_index=True` to status, uploaded_at, clause_type, severity, and is_resolved fields.
**Files Changed:** `contracts/models.py`

### Bug Fix 2: Custom Manager Added
**Problem:** Repeated filter queries scattered across views made code hard to maintain.
**Fix:** Added `DocumentManager` with reusable query methods: `pending()`, `completed()`, `with_high_risk()`.
**Files Changed:** `contracts/models.py`

### Bug Fix 3: Model Properties Added
**Problem:** Computing file_size_display, high_risk_count and is_processed required repeated code in serializers.
**Fix:** Added model properties: `is_processed`, `is_pending`, `file_size_display`, `high_risk_count`.
**Files Changed:** `contracts/models.py`

### Bug Fix 4: Logging Added
**Problem:** No logging meant errors were silent in production.
**Fix:** Added Django logging configuration with console and file handlers.
**Files Changed:** `legaltech_project/settings.py`

### Bug Fix 5: 409 Conflict for Re-processing
**Problem:** Re-processing a completed document returned 400 Bad Request which is not semantically correct.
**Fix:** Changed to return 409 Conflict with `DOCUMENT_ALREADY_PROCESSED` error code.
**Files Changed:** `contracts/exceptions.py`, `contracts/nlp_views.py`