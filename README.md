<div align="center">

# ⚖️ LegalTech — Automated Contract Parsing & Risk Extraction Engine

**An AI-powered backend system that reads legal contracts, extracts key clauses, and flags high-risk language — automatically.**

![Status](https://img.shields.io/badge/status-complete-brightgreen)
![Backend](https://img.shields.io/badge/backend-Django%20REST-darkgreen)
![Database](https://img.shields.io/badge/database-PostgreSQL-blue)
![Tests](https://img.shields.io/badge/tests-392%20passing-success)
![Docker](https://img.shields.io/badge/docker-ready-2496ED)
![Admin](https://img.shields.io/badge/admin-dashboard-orange)

[Quick Start](#-quick-start) •
[Features](#-features) •
[Screenshots](#-screenshots) •
[API Docs](docs/API_DOCUMENTATION.md) •
[Installation](#-installation)

</div>

---

## 📌 What Is This Project?

Corporate law firms manually review **thousands of contracts** every year looking for dangerous clauses. This process is slow, expensive, and error-prone.

**LegalTech automates this review:**
1. Upload a contract PDF
2. NLP engine extracts clauses and flags risks
3. Dashboard displays results for senior counsel

> **Goal:** Reduce contract review time by 70%

---

## ✨ Features

### For Administrators (Member 3)
- 📊 **Analytics Dashboard** — Real-time statistics with progress bars
- 📄 **Contract Management** — View, filter, search all contracts
- ⚠️ **Risk Monitoring** — Track high/medium/low severity risks
- 📑 **Clause Browser** — View all extracted clauses
- 📥 **CSV Export** — Export data for external analysis
- 🎨 **Professional UI** — Color-coded status badges and risk indicators

### For Developers (Member 1)
- 🔌 **17 REST API Endpoints** — Complete CRUD operations
- 🗄️ **PostgreSQL Database** — 3 normalized models with indexes
- 🛡️ **Input Validation** — Comprehensive error handling
- 🐳 **Docker Ready** — One-command deployment
- ✅ **392 Automated Tests** — Full test coverage

### For NLP Integration (Member 2)
- 🤖 **5 NLP Endpoints** — Dedicated API for NLP module
- 📦 **Atomic Transactions** — All-or-nothing data saves
- 🔄 **Status Tracking** — Monitor processing pipeline

---

## 📸 Screenshots

### Admin Analytics Dashboard
![Admin Dashboard](docs/SCREENSHOTS/admin-dashboard.png)
*Real-time statistics with processing status and risk breakdown*

### Contract List View
![Contract List](docs/SCREENSHOTS/contract-list.png)
*Filterable list with color-coded status badges*

### Document Detail with Inline Clauses
![Document Detail](docs/SCREENSHOTS/document-detail.png)
*View extracted clauses and risk flags inline*

### API Health Check
![API Health](docs/SCREENSHOTS/api-health.png)
*API status and endpoint documentation*

> **Note:** Add actual screenshots to `docs/SCREENSHOTS/` folder

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Docker & Docker Compose (optional)

### Option 1: Docker (Recommended)
```bash
# Clone repository
git clone https://github.com/Priyanka-p-nayak/legaltech-contract-parser.git
cd legaltech-contract-parser

# Start with Docker
docker-compose up --build

# Access
# Admin: http://localhost:8000/admin/
# API:   http://localhost:8000/api/v1/health/