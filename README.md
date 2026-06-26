<div align="center">

# ⚖️ LegalTech — Automated Contract Parsing & Risk Extraction Engine

**An AI-powered system that automatically reads legal contracts,
extracts key clauses, detects high-risk language, and presents
findings in a professional admin dashboard.**

![Status](https://img.shields.io/badge/status-active%20development-yellow)
![Backend](https://img.shields.io/badge/backend-Django%20REST-darkgreen)
![Database](https://img.shields.io/badge/database-PostgreSQL-blue)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Docker](https://img.shields.io/badge/docker-ready-2496ED)
![License](https://img.shields.io/badge/license-MIT-green)

[Quick Start](#-quick-start) •
[Features](#-features) •
[API Docs](#-api-documentation) •
[Team](#-team) •
[Docker](#-docker-setup)

</div>

---

## 📌 Problem Statement

Corporate law firms manually review **thousands of contracts
every year** — NDAs, MSAs, vendor agreements — searching for
dangerous clauses buried in dense legal language. This process
is **slow, expensive, and error-prone**. A single missed clause
like *"unlimited liability"* or an unfavorable governing
jurisdiction can cost companies millions.

**LegalTech automates this review** — reducing contract
review time by 70%.

---

## ✨ Features

### 🔵 Backend 
- ✅ PDF contract upload via REST API
- ✅ PostgreSQL database with 3 optimized models
- ✅ 17 REST API endpoints
- ✅ NLP integration endpoints for Member 2
- ✅ Dashboard data endpoint for Member 3
- ✅ Full error handling and input validation
- ✅ Pagination, filtering, search
- ✅ Docker containerization

### 🟢 NLP Engine 
- 🔄 PDF text extraction using PyMuPDF (Fitz)
- 🔄 Entity extraction using spaCy NLP
- 🔄 Clause categorization (Confidentiality, Termination, etc.)
- 🔄 Risk keyword detection (indemnify, unlimited liability, etc.)

### 🟡 Admin Dashboard 
- ✅ Professional Django Admin with colored badges
- ✅ Analytics dashboard with statistics
- ✅ CSV export for all contracts
- ✅ Bulk actions (mark as resolved, export)
- ✅ Inline clause and risk flag views
- ✅ Custom filters (risk level, resolution status)
- ✅ Comprehensive test suite
- ✅ Docker + docker-compose setup

---

## 🏗️ Architecture

```
┌─────────────────────┐     ┌──────────────────────────┐
│   Member 3          │     │      Member 1             │
│   Admin Dashboard   │────▶│   Django REST Backend     │
│   (This file)       │     │   (PostgreSQL + APIs)     │
└─────────────────────┘     └────────────┬─────────────┘
                                         │
                              ┌──────────▼─────────────┐
                              │      Member 2           │
                              │   NLP Engine            │
                              │   (PyMuPDF + spaCy)     │
                              └─────────────────────────┘
```

---

## 👥 Team

| Member | Role | Responsibilities |
|---|---|---|
| **Member 1** | Backend Developer | Django, PostgreSQL, REST APIs, Docker |
| **Member 2** | NLP Engineer | PyMuPDF, spaCy, Entity Extraction, Risk Detection |
| **Member 3** | Full Stack / DevOps | Admin Dashboard, Testing, Documentation, Docker |

---

## 🛠️ Technology Stack

| Component | Technology | Version |
|---|---|---|
| Backend Framework | Django + DRF | 4.x |
| Database | PostgreSQL | 15 |
| NLP Engine | spaCy | 3.x |
| PDF Processing | PyMuPDF (Fitz) | Latest |
| Admin Dashboard | Django Admin | Built-in |
| Containerization | Docker + Compose | Latest |
| Language | Python | 3.11 |
| API Testing | Postman | Latest |

---

## 🚀 Quick Start

### Option 1: Run with Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/Priyanka-p-nayak/legaltech-contract-parser.git
cd legaltech-contract-parser

# Copy environment file
cp .env.example .env

# Build and run everything
docker-compose up --build
```

Access:
- **API:** `http://localhost:8000/api/v1/health/`
- **Admin:** `http://localhost:8000/admin/`
- **Dashboard:** `http://localhost:8000/admin/stats/`

---

### Option 2: Run Locally

```bash
# Clone repository
git clone https://github.com/Priyanka-p-nayak/legaltech-contract-parser.git
cd legaltech-contract-parser

# Create virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Start server
python manage.py runserver
```

---

## 🗄️ Database Models

### Document
Represents an uploaded PDF contract.

| Field | Type | Description |
|---|---|---|
| `file_name` | CharField | Original PDF filename |
| `file` | FileField | Stored PDF path |
| `contract_type` | CharField | NDA, MSA, Employment, etc. |
| `counterparty_name` | CharField | Other party in contract |
| `governing_law` | CharField | Legal jurisdiction |
| `status` | CharField | uploaded/processing/completed/failed |
| `risk_score` | IntegerField | Total risk count from NLP |
| `uploaded_at` | DateTimeField | Upload timestamp |

### ExtractedClause
One row per legal clause extracted by Member 2's NLP.

| Field | Type | Description |
|---|---|---|
| `document` | ForeignKey | Parent contract |
| `clause_type` | CharField | confidentiality, termination, etc. |
| `clause_text` | TextField | Full extracted text |
| `page_number` | IntegerField | Page in PDF |
| `confidence_score` | FloatField | NLP confidence (0.0–1.0) |

### RiskFlag
One row per risky clause detected by Member 2's NLP.

| Field | Type | Description |
|---|---|---|
| `document` | ForeignKey | Parent contract |
| `risk_title` | CharField | Short risk description |
| `flagged_text` | TextField | Exact risky sentence |
| `keyword_matched` | CharField | Trigger keyword |
| `severity` | CharField | low / medium / high |
| `is_resolved` | BooleanField | Reviewed by counsel |

---

## 🔗 API Endpoints

Base URL: `http://127.0.0.1:8000/api/v1/`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health/` | API health check |
| GET | `/stats/` | System statistics |
| GET | `/dashboard/` | Dashboard overview |
| POST | `/documents/upload/` | Upload PDF |
| GET | `/documents/` | List all documents |
| GET | `/documents/{id}/` | Document detail |
| PATCH | `/documents/{id}/update-status/` | Update status |
| POST | `/documents/{id}/clauses/` | Save clauses |
| GET | `/documents/{id}/clauses/` | Get clauses |
| POST | `/documents/{id}/risks/` | Save risk flags |
| GET | `/documents/{id}/risks/` | Get risk flags |
| GET | `/nlp/documents/pending/` | NLP pending queue |
| POST | `/nlp/documents/{id}/process/` | Submit NLP results |

Full API documentation: [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md)

---

## 🧪 Running Tests

```bash
# Run all tests
python manage.py test contracts.tests --verbosity=2

# Run specific test file
python manage.py test contracts.tests.test_models
python manage.py test contracts.tests.test_admin
python manage.py test contracts.tests.test_views

# Run with coverage
pip install coverage
coverage run manage.py test contracts.tests
coverage report
```

---

## 🐳 Docker Setup

```bash
# Development (with pgAdmin)
docker-compose -f docker-compose.yml \
               -f docker-compose.dev.yml up --build

# Access pgAdmin: http://localhost:5050
# Email: admin@legaltech.com / Password: admin123
```

See full Docker guide: [`docs/DOCKER_GUIDE.md`](docs/DOCKER_GUIDE.md)

---

## 📁 Project Structure

```
legaltech_project/
├── contracts/                    # Main Django app
│   ├── models.py                 # 3 database models
│   ├── views.py                  # 9 API views
│   ├── nlp_views.py              # 5 NLP endpoints
│   ├── views_admin.py            # Admin stats view
│   ├── admin.py                  # Admin configuration
│   ├── serializers.py            # DRF serializers
│   ├── validators.py             # Input validators
│   ├── exceptions.py             # Custom exceptions
│   ├── pagination.py             # Pagination classes
│   ├── urls.py                   # URL routing
│   └── tests/                   # Test suite
│       ├── test_models.py
│       ├── test_views.py
│       ├── test_admin.py
│       └── test_integration.py
├── legaltech_project/            # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── error_handlers.py
├── templates/                    # HTML templates
│   └── admin/contracts/
│       └── dashboard.html
├── docs/                         # Documentation
│   ├── API_DOCUMENTATION.md
│   ├── DATABASE_MODELS.md
│   └── DOCKER_GUIDE.md
├── integration/                  # Integration tests
├── postman/                      # Postman collection
├── nginx/                        # Nginx config
├── scripts/                      # Utility scripts
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔒 Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

| Variable | Description | Example |
|---|---|---|
| `SECRET_KEY` | Django secret key | `your-secret-key-here` |
| `DEBUG` | Debug mode | `True` |
| `DB_NAME` | Database name | `legaltech_db` |
| `DB_USER` | DB username | `postgres` |
| `DB_PASSWORD` | DB password | `your-password` |
| `DB_HOST` | DB host | `localhost` |
| `DB_PORT` | DB port | `5432` |

---

## 🔮 Future Improvements

- [ ] JWT Authentication for API endpoints
- [ ] Email notifications when high-risk contracts are found
- [ ] PDF viewer embedded in admin
- [ ] Bulk PDF upload support
- [ ] Contract comparison feature
- [ ] Export reports as PDF
- [ ] Role-based access (paralegal vs senior counsel)
- [ ] Audit log for all admin actions
- [ ] API rate limiting per user
- [ ] Machine learning risk scoring

---

## 📸 Screenshots

### Admin Dashboard
*(Screenshots will be added after full deployment)*

### API Health Check
```json
{
    "success": true,
    "message": "LegalTech API is running successfully.",
    "data": {
        "api_version": "1.0.0",
        "status": "healthy"
    }
}
```

---

## 📄 License

This project is built as an internship project for
**Infotact Solutions & Co.**

---

<div align="center">
Built with ❤️ by the LegalTech Team — Infotact Solutions Internship 2026
</div>