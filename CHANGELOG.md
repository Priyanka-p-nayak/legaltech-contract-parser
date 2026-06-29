# CHANGELOG — LegalTech Contract Parser Backend

All significant work by **Member 1 (Backend, Database & APIs)**.
Format: `[Day N — Date] Short description`

---

## Week 1 — Django Setup + Database + Core Models (June 7–13)

### Day 1 — June 7
- Initialized Django project (`legaltech_project`)
- Connected PostgreSQL database (`legaltech_db`)
- Created virtual environment and installed core dependencies
- Configured `settings.py` with environment variables via `python-dotenv`
- Created `.gitignore` and `.env` files
- Created `contracts` Django app
- First commit pushed to GitHub

### Day 2 — June 8
- Created `Document` model with 12 fields
- Configured `DocumentAdmin` with list display, search, filters
- Ran initial migrations to create `contracts_document` table
- Verified model in Django Admin panel

### Day 3 — June 9
- Created `ExtractedClause` model with `ForeignKey → Document (CASCADE)`
- Created `RiskFlag` model with `ForeignKey → Document (CASCADE)`
- Configured `ExtractedClauseAdmin` and `RiskFlagAdmin`
- Ran migrations to create both new tables
- Verified all 3 models in Django Admin

### Day 4 — June 10
- Created 6 DRF serializers:
  - `ExtractedClauseSerializer`, `RiskFlagSerializer`
  - `DocumentListSerializer`, `DocumentDetailSerializer`
  - `DocumentUploadSerializer`, `DocumentStatusUpdateSerializer`
- Added field-level validation (confidence_score, page_number, clause_text)
- Tested serializers in Django shell

### Day 5 — June 11
- Created 7 API views in `views.py`
- Created `contracts/urls.py` with all URL patterns
- Updated main `legaltech_project/urls.py`
- Configured REST_FRAMEWORK settings and MEDIA file settings
- Health check endpoint: `GET /api/v1/health/`
- PDF upload endpoint: `POST /api/v1/documents/upload/`

### Day 6 — June 12
- Added GET endpoints: list, detail, summary, stats
- Added filtering, search, and ordering to document list
- Added NLP result endpoints (clauses GET, risks GET)
- Created and saved Postman collection with 11 API tests
- Full manual Postman test run — all endpoints verified

### Day 7 — June 13
- Created `contracts/exceptions.py` with 8 custom exception classes
- Created `contracts/validators.py` with 7 reusable validator functions
- Created `legaltech_project/error_handlers.py` (global exception handler)
- Updated `settings.py` to use custom exception handler
- Updated all views to use validators and exceptions
- Tested all error responses in Postman

---

## Week 2 — APIs + NLP Integration (June 14–20)

### Day 8 — June 14
- Created `contracts/nlp_views.py` with 5 NLP-specific endpoints:
  - `GET /api/v1/nlp/documents/pending/`
  - `GET /api/v1/nlp/documents/{id}/`
  - `POST /api/v1/nlp/documents/{id}/process/`
  - `PATCH /api/v1/nlp/documents/{id}/status/`
  - `GET /api/v1/nlp/documents/{id}/results/`
- Updated `urls.py` to register all NLP routes
- Tested complete NLP integration flow in Postman

### Day 9 — June 15
- Created `contracts/pagination.py` (StandardPagination + SmallPagination)
- Updated `settings.py` with pagination configuration
- Added API versioning: all endpoints now under `/api/v1/`
- Updated `legaltech_project/urls.py` to mount under `/api/v1/`
- Updated all views to use paginator

### Day 10 — June 16
- Created `contracts/tests/test_views.py` (47 unit tests)
- Polished validators with full edge-case coverage
- Polished serializers with stronger field validation
- Full test run: all 47 tests passing

### Day 11 — June 17
- Final URL routing cleanup and naming standardization
- Created `postman/LegalTech_API.json` — full collection with 6 request groups
- Started `README.md` with project setup instructions and endpoint table
- All APIs re-tested post-cleanup

### Day 12 — June 18
- Created `integration/` folder with `__init__.py`
- Created `integration/mock_nlp.py` — live NLP simulation script
- Created `integration/test_integration.py` (5 integration tests)
- Installed `requests` library for the simulation script
- Verified full upload → NLP → results flow with mock script

### Day 13 — June 19
- Final settings review and cleanup
- Created `CHECKLIST.md` with mid-review status
- Updated README with final pre-review status
- Full test run (52 tests) — all passing
- Mid-review preparation complete

### Day 14 — June 20
- Installed and configured `django-cors-headers`
- Added CORS settings to `settings.py` (initial `CORS_ALLOW_ALL_ORIGINS=True`)
- Created `docs/API_DOCUMENTATION.md` (initial version)
- Created `docs/DOCKER_GUIDE.md` (initial version)
- Mid-review day — feedback incorporated

---

## Week 3 — Testing + Docker + Integration (June 21–30)

### Day 15 — June 21
- Reorganized tests into `contracts/tests/` folder structure
- Created `contracts/tests/test_models.py` (~45 tests)
- Created `contracts/tests/test_serializers.py` (~25 tests)
- Moved old `tests.py` content to `test_views.py`
- Total tests: ~85 passing

### Day 16 — June 22
- Rewrote `contracts/tests/test_views.py` with deep per-endpoint tests (~75 tests)
- Created `contracts/tests/test_nlp_views.py` (~40 tests)
- Total tests: ~160 passing

### Day 17 — June 23
- Added edge case handling in `views.py` (bulk limits, text length limits)
- Updated `validators.py` with additional validators
- Created `contracts/tests/test_edge_cases.py` (~70 tests)
- Total tests: ~230 passing

### Day 18 — June 24
- Updated all exception classes with proper HTTP status codes
- Added 409 Conflict for `DocumentAlreadyProcessedException`
- Added 413 Payload Too Large for `FileTooLargeException`
- Updated `error_handlers.py` with custom 404/500 handlers
- Created `contracts/tests/test_status_codes.py` (~55 tests)
- Created `docs/STATUS_CODES.md`
- Total tests: ~280 passing

### Day 19 — June 25
- Added database indexes to `Document`, `ExtractedClause`, `RiskFlag`
- Added `DocumentManager` with 4 custom query methods
- Added 7 model properties (`is_processed`, `is_pending`, `file_size_display`, etc.)
- Added Django `LOGGING` configuration
- Created `contracts/tests/test_performance.py` (~30 tests)
- Created `docs/BUG_FIXES.md`
- Total tests: ~310 passing

### Day 20 — June 26
- Created `Dockerfile` (Python 3.11-slim base)
- Created `docker-entrypoint.sh` startup script
- Created initial `docker-compose.yml`
- Created `.dockerignore`
- Installed `gunicorn`
- Verified `docker-compose up --build` works end to end

### Day 21 — June 27
- Created `docker-compose.dev.yml` (with pgAdmin service)
- Created `docker-compose.prod.yml` (with Nginx service)
- Created `nginx/nginx.conf` and `nginx/default.conf`
- Created `scripts/` folder (dev.sh, prod.sh, stop.sh, reset.sh)
- Created `scripts/init_db.sql`
- Updated `docker-entrypoint.sh` with colour output and error handling
- Created `.env.example`
- Updated `docs/DOCKER_GUIDE.md`

### Day 22 — June 28
- Verified and hardened CORS settings
- Added `DashboardOverviewView` (`GET /api/v1/dashboard/`)
- Added `/api/v1/dashboard/` URL to `urls.py`
- Created `contracts/tests/test_dashboard.py` (~35 tests)
- Created `docs/MEMBER3_GUIDE.md`
- Created `docs/dashboard_sample.js`
- Total tests: ~345 passing

### Day 23 — June 29
- Created `integration/test_full_system.py` (6 tests: 12-stage workflow)
- Created `integration/full_simulation.py` (live runnable demo)
- Created `docs/INTEGRATION_REPORT.md`
- Full system integration test: all 12 stages passing

### Day 24 — June 30
- Found and fixed 7 cross-module integration bugs:
  1. `total_clauses_count`/`total_risks_count` duplicated logic
  2. `DashboardOverviewView` had its own duplicate counting
  3. `StatsView.risks_by_severity` omitted zero-count severities
  4. `StatsView.documents_by_status` omitted zero-count statuses
  5. `NLPProcessResultView` had no bulk size limit
  6. Invalid `?ordering=` gave no feedback
  7. Invalid `?severity=` silently returned empty results
- Created `contracts/tests/test_integration_bugfixes.py` (~25 tests)
- Created `docs/BUG_FIXES_DAY24.md`
- Total tests: ~316 passing

---

## Week 4 — Documentation + Optimization + Security (July 1–8)

### Day 25 — July 1
- Rewrote `README.md` overview section with:
  - Badges (status, backend, database, tests, docker)
  - "What Is This?" and "Who Is This For?" sections
  - Full 3-member architecture diagram
  - "My Role — Member 1" detailed summary
  - Project Status table
  - Expandable Table of Contents

### Day 26 — July 2
- Rewrote `docs/API_DOCUMENTATION.md` with:
  - Quick Reference Table (all 17 endpoints)
  - curl commands for every single endpoint
  - 3 common workflow sequences
  - Performance notes
  - Cross-links to README and Member 3 guide

### Day 27 — July 3
- Created `docs/DATABASE_MODELS.md` with:
  - Full ER diagram (text-based, GitHub-renderable)
  - Every field documented (type, nullable, default, WHY)
  - Relationships explained (CASCADE, related_names)
  - 8 database indexes documented
  - 4 custom manager methods documented
  - 7 model properties documented
  - Example JSON rows for each model
  - 4 design decision explanations (WHY PostgreSQL, etc.)

### Day 28 — July 4
- Added module docstrings to all 12 backend Python files
- Added "WHY" inline comments to all non-obvious decisions
- Standardized section header comment style across all files
- Created `docs/CODING_STANDARDS.md`

### Day 29 — July 5
- Fixed N+1 query problems on 4 endpoints:
  - `DashboardOverviewView` — `prefetch_related('clauses', 'risk_flags')`
  - `DocumentListView` — `prefetch_related('clauses', 'risk_flags')`
  - `DocumentDetailView` — `prefetch_related` on single-object fetch
  - `NLPResultsView` — audited, confirmed safe (no change needed)
- Fixed subtle `.count()` vs `len()` prefetch-cache issue in model properties
- Created `contracts/tests/test_query_optimization.py` (11 tests)
- Created `docs/QUERY_OPTIMIZATION_REPORT.md`
- Total tests: ~327 passing

### Day 30 — July 6
- Replaced `CORS_ALLOW_ALL_ORIGINS=True` with explicit `CORS_ALLOWED_ORIGINS` list
- Added security headers: `X_FRAME_OPTIONS`, `SECURE_CONTENT_TYPE_NOSNIFF`,
  `SECURE_BROWSER_XSS_FILTER`
- Added production HTTPS settings (conditional on `not DEBUG`)
- Added `CONN_MAX_AGE=60` to database configuration
- Created `legaltech_project/management/commands/security_check.py`
- Created `contracts/tests/test_security.py` (~18 tests)
- Created `docs/SECURITY.md`
- Total tests: ~345 passing

### Day 31 — July 7
- Final test pass: identified and fixed stale query count assertions
- Created `contracts/tests/test_final.py` (47 smoke tests)
- Updated `postman/LegalTech_API.json` with dashboard and security groups
- Created `docs/TEST_SUMMARY.md`
- Total tests: ~392 passing

### Day 32 — July 8
- Dead code audit using `pyflakes`
- Removed all unused imports across 12 files
- Moved all inline `from ... import` statements to file-level imports
- Standardized 2-blank-line class separation, 1-blank-line method separation
- Verified no `print()` debug statements remain
- Cleared all TODO/FIXME comments
- Created `CHANGELOG.md` (this file)
- **Final submission commit**

---

## Summary Statistics

| Metric | Value |
|---|---|
| Total Days | 32 |
| GitHub Commits | 32+ |
| Python Files Written | 20+ |
| API Endpoints | 17 |
| Database Models | 3 |
| DRF Serializers | 6 |
| Automated Tests | ~392 |
| Documentation Files | 10+ |
| Docker Files | 8 |
| Lines of Code (est.) | 6,000+ |

---

> 🏠 Back to [Project README](README.md)