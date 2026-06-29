# Project Structure — LegalTech Contract Parser

## Root Directory

```
legaltech-contract-parser/
│
├── 📁 contracts/          → Main Django application
├── 📁 legaltech_project/  → Django project settings
├── 📁 templates/          → HTML templates
├── 📁 docs/               → All documentation
├── 📁 integration/        → Integration tests
├── 📁 postman/            → Postman API collection
├── 📁 nginx/              → Nginx reverse proxy config
├── 📁 scripts/            → Helper shell scripts
├── 📁 media/              → Uploaded PDF files
├── 📁 logs/               → Application logs
│
├── 📄 manage.py           → Django management CLI
├── 📄 Dockerfile          → Container definition
├── 📄 docker-compose.yml  → Multi-service orchestration
├── 📄 requirements.txt    → Python dependencies
├── 📄 .env.example        → Environment variables template
└── 📄 README.md           → Project overview
```

---

## `contracts/` App (Core Application)

```
contracts/
├── __init__.py
├── apps.py               → App configuration
│
├── models.py             → Database models (Member 1)
│                           - Document
│                           - ExtractedClause
│                           - RiskFlag
│
├── admin.py              → Admin dashboard (Member 3)
│                           - DocumentAdmin
│                           - ExtractedClauseAdmin
│                           - RiskFlagAdmin
│
├── views.py              → API views (Member 1)
│                           - DocumentUploadView
│                           - DocumentListView
│                           - DocumentDetailView
│                           - DashboardOverviewView
│                           - StatsView
│
├── nlp_views.py          → NLP endpoints (Member 1)
│                           - NLPPendingDocumentsView
│                           - NLPProcessResultView
│                           - NLPResultsView
│
├── views_admin.py        → Admin stats view (Member 3)
│                           - admin_dashboard_stats
│
├── serializers.py        → Data serialization (Member 1)
│                           - DocumentListSerializer
│                           - DocumentDetailSerializer
│                           - ExtractedClauseSerializer
│                           - RiskFlagSerializer
│
├── validators.py         → Input validation (Member 1)
│                           - validate_pdf_file
│                           - validate_document_status
│
├── exceptions.py         → Custom exceptions (Member 1)
│                           - InvalidFileTypeException
│                           - FileTooLargeException
│
├── pagination.py         → List pagination (Member 1)
│                           - StandardPagination
│
├── urls.py               → URL routing (Member 1/3)
│
├── migrations/           → Database migrations (auto-generated)
│   ├── 0001_initial.py
│   └── 0002_add_indexes.py
│
└── tests/                → Test suite (Member 3)
    ├── __init__.py
    ├── test_models.py    → Model unit tests
    ├── test_views.py     → API endpoint tests
    ├── test_admin.py     → Admin panel tests
    └── test_integration.py → End-to-end tests
```

### What Each File Does

**`models.py`** — Defines the database structure
- `Document` — Represents an uploaded PDF contract
- `ExtractedClause` — One extracted legal clause
- `RiskFlag` — One detected risk

**`admin.py`** — Configures the Django Admin interface
- Customizes how models appear in the admin panel
- Adds filters, search, and custom actions
- Member 3's responsibility

**`views.py`** — API endpoint logic
- Handles HTTP requests (GET, POST, PATCH, DELETE)
- Validates input, queries database, returns JSON
- Member 1's responsibility

**`nlp_views.py`** — NLP integration endpoints
- Endpoints that Member 2's NLP module will call
- Handles pending document queue
- Processes NLP results

**`serializers.py`** — Data conversion
- Converts Django models to JSON (for API responses)
- Converts JSON to Django models (for API requests)
- Validates data

**`validators.py`** — Input validation
- Checks if file is a PDF
- Validates file size
- Ensures data integrity

**`exceptions.py`** — Custom error handling
- Defines custom exception classes
- Provides clear error messages

**`pagination.py`** — List pagination
- Controls how many items per page
- Adds next/previous links

**`urls.py`** — URL routing
- Maps URLs to views
- Example: `/api/v1/documents/` → `DocumentListView`

---

## `legaltech_project/` (Project Settings)

```
legaltech_project/
├── __init__.py
├── settings.py           → Project configuration
├── urls.py               → Root URL configuration
├── wsgi.py               → WSGI application (for production)
└── error_handlers.py     → Global error handlers
```

**`settings.py`** — Main configuration file
- Database connection settings
- Installed apps
- Middleware configuration
- Security settings

**`urls.py`** — Root URL routing
- Includes app URLs from `contracts/urls.py`
- Routes `/admin/` to Django Admin

---

## `templates/` (HTML Templates)

```
templates/
└── admin/
    └── contracts/
        └── dashboard.html    → Custom admin dashboard
```

**What are templates?**
HTML files that Django renders with dynamic data.

**`dashboard.html`** — Custom statistics dashboard
- Shows contract statistics
- Displays risk breakdowns
- Member 3's responsibility

---

## `docs/` (Documentation)

```
docs/
├── API_DOCUMENTATION.md      → Complete API reference
├── DATABASE_MODELS.md        → Database schema details
├── DOCKER_GUIDE.md           → Docker setup instructions
├── INSTALLATION_GUIDE.md     → Installation steps
├── PROJECT_STRUCTURE.md      → This file
└── MEMBER3_GUIDE.md          → Dashboard integration guide
```

---

## `integration/` (Integration Tests)

```
integration/
├── __init__.py
├── test_integration.py       → Integration test suite
├── test_full_system.py       → Full system workflow test
├── mock_nlp.py               → Mock NLP module for testing
└── full_simulation.py        → End-to-end simulation
```

**What are integration tests?**
Tests that verify multiple components work together.

**`mock_nlp.py`** — Simulates Member 2's NLP module
- Calls the NLP endpoints
- Sends mock extracted data
- Tests the integration flow

---

## `postman/` (API Testing)

```
postman/
└── LegalTech_API.json        → Postman collection
```

**What is Postman?**
A tool for testing APIs manually.

**`LegalTech_API.json`** — Pre-configured API requests
- Import this into Postman
- Test all 17 endpoints
- See example requests/responses

---

## `nginx/` (Reverse Proxy)

```
nginx/
├── nginx.conf                → Main Nginx configuration
└── default.conf              → Virtual host configuration
```

**What is Nginx?**
A web server that sits in front of Django.

**Why use Nginx?**
- Serves static files efficiently
- Handles HTTPS
- Load balancing (for production)

---

## `scripts/` (Helper Scripts)

```
scripts/
├── dev.sh                    → Start development environment
├── prod.sh                   → Start production environment
├── stop.sh                   → Stop all containers
└── reset.sh                  → Reset database and containers
```

**What are these scripts?**
Shell scripts that automate common tasks.

**Example usage:**
```bash
./scripts/dev.sh    # Start development
./scripts/stop.sh   # Stop everything
```

---

## Data Flow

```
1. User uploads PDF via API (POST /api/v1/documents/upload/)
   ↓
2. Member 1 saves Document record in PostgreSQL
   ↓
3. Member 2 polls GET /api/v1/nlp/documents/pending/
   ↓
4. Member 2 extracts text using PyMuPDF
   ↓
5. Member 2 runs spaCy NLP on extracted text
   ↓
6. Member 2 sends results to POST /api/v1/nlp/documents/{id}/process/
   ↓
7. Member 1 saves ExtractedClause + RiskFlag records
   ↓
8. Member 3's Admin shows everything in the dashboard
```

---

## File Ownership

| File/Folder | Owner | Purpose |
|---|---|---|
| `models.py` | Member 1 | Database structure |
| `views.py` | Member 1 | API logic |
| `nlp_views.py` | Member 1 | NLP integration |
| `serializers.py` | Member 1 | Data conversion |
| `validators.py` | Member 1 | Input validation |
| `exceptions.py` | Member 1 | Error handling |
| `admin.py` | Member 3 | Admin dashboard |
| `views_admin.py` | Member 3 | Admin views |
| `templates/` | Member 3 | HTML templates |
| `tests/` | Member 3 | Test suite |
| `docs/` | Member 3 | Documentation |
| `integration/` | Member 3 | Integration tests |

---

## Quick Navigation

**Looking for...** | **Go to...**
---|---
Database models | `contracts/models.py`
API endpoints | `contracts/views.py`
Admin configuration | `contracts/admin.py`
URL routing | `contracts/urls.py`
Test suite | `contracts/tests/`
Project settings | `legaltech_project/settings.py`
Documentation | `docs/`
Docker setup | `Dockerfile` + `docker-compose.yml`