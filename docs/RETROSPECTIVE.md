# Project Retrospective — Member 1 (Backend)

**Project:** LegalTech — Automated Contract Parsing & Risk Extraction Engine  
**Role:** Member 1 — Django Backend, PostgreSQL, REST APIs  
**Period:** June 7 – July 10, 2026 (34 days)  
**Org:** Infotact Solutions & Co. Internship

---

## What I Built

A complete Django REST API backend that:

- Accepts uploaded PDF contracts from a dashboard UI
- Stores them in a PostgreSQL database
- Exposes dedicated endpoints for an NLP module to submit extracted clauses and risk flags
- Exposes dedicated endpoints for a dashboard UI to display processed contract data
- Handles errors, validation, pagination, and security consistently across all endpoints

### By the Numbers

| Metric | Count |
|---|---|
| Days worked | 34 |
| GitHub commits | 34+ |
| API endpoints built | 17 |
| Database models | 3 |
| DRF serializers | 6 |
| Automated tests | ~501 |
| Test files | 14 |
| Documentation files | 15 |
| Docker configuration files | 6 |
| Lines of Python written | ~6,000 |

---

## Week-by-Week Summary

### Week 1 (Days 1–7): Foundation
Set up Django + PostgreSQL, created 3 database models, configured Django Admin, built 6 DRF serializers with validation, created the first 11 API endpoints including PDF upload. First real backend-to-database flow working.

**Hardest part:** Understanding Django's ORM relationships (`ForeignKey`, `CASCADE`, `related_name`) and how they translate to the actual SQL tables.

**Key learning:** Writing `related_name='clauses'` on the ForeignKey means writing `document.clauses.all()` everywhere instead of Django's default verbose `extractedclause_set`. Small decision, enormous readability improvement.

### Week 2 (Days 8–14): NLP Integration + API Maturity
Built the 5 NLP-specific endpoints in a separate file, added API versioning (`/api/v1/`), added pagination, wrote the first 52 automated tests, created the Postman collection, and completed the mid-review. Also created the first mock NLP simulation script to prove the Member 2 integration worked without needing Member 2's actual code.

**Hardest part:** Understanding Django's URL namespace system and making sure all 16 URL patterns resolved correctly after adding the `/api/v1/` prefix.

**Key learning:** Separating NLP endpoints into `nlp_views.py` was one of the best architectural decisions of the project. It made the integration story clear for Member 2 — they just read one file and know everything they need.

### Week 3 (Days 15–24): Testing + Docker + Integration
The biggest testing push — went from 52 tests to ~316. Added edge case tests, status code tests, performance tests, and integration bug tests. Containerized the project with Docker and docker-compose. Added the dashboard endpoint for Member 3. Found and fixed 7 cross-module integration bugs during a full code audit.

**Hardest part:** Finding Bug 3 and 4 from Day 24 — `StatsView` was omitting zero-count severities from the response, which would cause Member 3's chart code to crash on `undefined.count` whenever a severity had no risks. It was invisible in all the normal test cases because there were always at least some risks of each severity in test data.

**Key learning:** Write tests that specifically create EMPTY/ZERO scenarios. The bug was only visible when a severity had zero risks — a common real-world case, but never tested until Day 24.

### Week 4 (Days 25–34): Documentation + Optimization + Security
Documentation week. Rewrote README with architecture diagram, wrote full API docs with curl commands, wrote deep-dive database model docs, standardized all inline comments, fixed N+1 query problems with `prefetch_related`, hardened CORS and security headers, wrote ~47 final smoke tests, and wrote the review preparation guides.

**Hardest part:** The `len()` vs `.count()` distinction on prefetched querysets (Day 29). The optimization wasn't working even after adding `prefetch_related` because `.count()` still issued a fresh SQL query even on prefetched relations in our Django version. Using `len(queryset.all())` instead was the non-obvious fix.

**Key learning:** Django's ORM has surprising behaviors around prefetch caching. Always verify with `assertNumQueries` that your optimization is actually reducing query counts — not just that the code looks like it should be optimized.

---

## What I'm Most Proud Of

### 1. The NLP integration design
The `POST /api/v1/nlp/documents/{id}/process/` endpoint accepts clauses, risk flags, metadata, and status all in one `transaction.atomic()` call. No partial states, no race conditions, no "document shows completed but has no clauses" scenarios. Getting the atomic transaction right was important.

### 2. The cross-module bug fixes (Day 24)
Finding 7 integration bugs by deliberately comparing how different parts of the code calculated the same thing was genuinely satisfying detective work. The `total_clauses_count` / `total_risks_count` model properties created a single source of truth that prevented 3 different views from ever disagreeing about the same number again.

### 3. The query optimization (Day 29)
Going from 47 database queries to 10 queries on the dashboard endpoint, and then proving it with `assertNumQueries` tests that specifically check the query count DOESN'T GROW with more data — that's the right way to verify an optimization.

### 4. The test suite structure
14 test files, each covering a specific concern, growing incrementally from Day 10 to Day 31. The final `test_final.py` smoke test that hits all 17 endpoints in sequence is something I'd be comfortable leaving to run in a CI pipeline.

---

## What I Would Do Differently

### 1. Add `select_related`/`prefetch_related` from Day 1
I added performance optimization on Day 29 — almost at the end. In a real project, I'd write the optimization alongside the initial view, not as a separate pass weeks later. The `assertNumQueries` regression tests are now there to catch regressions, but the ideal is to never introduce the N+1 pattern in the first place.

### 2. Write edge case tests BEFORE writing the code
I wrote tests on Day 10 after the code was done. In a real TDD workflow, you write the failing test first, then write code to make it pass. This would have caught the zero-count Stats bug on Day 10 instead of Day 24.

### 3. Add inline `WHY` comments as you write, not as a separate pass
Day 28 was a dedicated comment cleanup pass. Good comments written as you go — documenting the `why` immediately when you make a non-obvious decision — would have saved a full day and produced better comments because the reasoning is freshest when you write the code.

### 4. Set up Docker from Day 1
Docker was added on Day 20. In a professional project, the development environment would be containerized from Day 1 so every team member runs identical environments and "it works on my machine" never happens.

---

## Technical Skills Gained

### Before this project I knew:
- Basic Python and some Django tutorials
- What REST APIs are in theory
- Some database concepts

### After this project I can:
- Design and implement a normalized relational database schema with proper indexes, relationships, and constraints
- Build a production-quality Django REST API with DRF
- Write serializers that validate input at multiple levels
- Handle errors consistently across an entire API
- Write comprehensive automated tests (unit, integration, edge cases)
- Use `select_related`/`prefetch_related` to solve N+1 problems
- Containerize a Django+PostgreSQL project with Docker
- Write technical documentation that non-technical readers can understand
- Read HTTP responses and status codes fluently
- Use `git` daily with meaningful, organized commit messages

---

## Key Technical Concepts Learned

| Concept | Where Used |
|---|---|
| Django ORM relationships (FK, CASCADE, related_name) | All 3 models |
| DRF serializers + field validation | All 6 serializers |
| Custom exception handling (global handler) | error_handlers.py |
| API versioning | /api/v1/ URL structure |
| Pagination (page-based, configurable size) | Document list |
| `transaction.atomic()` for multi-step DB writes | NLP process endpoint |
| `prefetch_related` + `select_related` for N+1 | Dashboard + detail views |
| `assertNumQueries` for query regression testing | test_query_optimization.py |
| Django management commands | security_check.py |
| Docker multi-stage compose (dev/prod) | docker-compose files |
| HTTP semantic status codes (400 vs 409 vs 413) | All error responses |
| CORS configuration for cross-origin API calls | settings.py |
| Security headers (X-Frame-Options, nosniff) | settings.py + tests |

---

## Final State

The backend is complete and production-ready:

✅ 17 API endpoints — all working, all tested  
✅ 3 PostgreSQL models — with indexes and constraints  
✅ ~501 automated tests — all passing  
✅ Docker setup — one command to run everything  
✅ Security hardening — CORS, headers, audit command  
✅ Query optimization — N+1 bugs fixed and locked in  
✅ Full documentation — 15 docs files  
✅ 34 GitHub commits — one per day, meaningful messages

---

> Built with Django, PostgreSQL, Django REST Framework, Docker, and a lot of daily commits.

---

> 🏠 Back to [Project README](../README.md)