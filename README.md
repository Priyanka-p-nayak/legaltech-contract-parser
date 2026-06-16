
# LegalTech — Automated Contract Parsing & Risk Extraction Engine

Automated Legal Document Parsing Engine built with Django,
PostgreSQL, PyMuPDF, and spaCy.

---

## 👥 Team

| Member | Responsibility |
|---|---|
| Member 1 (Priyanka) | Django Backend + PostgreSQL + APIs |
| Member 2 | PDF Extraction + NLP (spaCy) |
| Member 3 | Dashboard + Documentation + Testing |

---

## 🛠️ Tech Stack (Member 1)

| Component | Technology |
|---|---|
| Backend Framework | Django 4.x + Django REST Framework |
| Database | PostgreSQL |
| File Handling | Pillow |
| Environment | python-dotenv |
| Testing | Django TestCase + APIClient |

---

## ⚙️ Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/Priyanka-p-nayak/legaltech-contract-parser.git
cd legaltech-contract-parser

---

## 🔗 Integration Guide for Member 2

### How to connect your NLP module to the backend:

**Step 1:** Call this to get pending documents:
GET /api/v1/nlp/documents/pending/

**Step 2:** Mark document as processing:
PATCH /api/v1/nlp/documents/{id}/status/

Body:
```json
{"status": "processing"}

**Step 3:** Submit all results in ONE call:
POST /api/v1/nlp/documents/{id}/process/
{
    "status": "completed",
    "risk_score": 3,
    "metadata": {
        "counterparty_name": "Company Name",
        "governing_law": "California",
        "contract_start_date": "2024-01-01",
        "contract_end_date": "2025-12-31"
    },
    "clauses": [
        {
            "clause_type": "confidentiality",
            "clause_text": "Full clause text here...",
            "page_number": 2,
            "confidence_score": 0.95
        }
    ],
    "risk_flags": [
        {
            "risk_title": "Unlimited Liability Found",
            "flagged_text": "Exact risky text...",
            "keyword_matched": "unlimited liability",
            "severity": "high",
            "page_number": 4,
            "explanation": "Why this is risky..."
        }
    ]
}

**Step 4:** Verify your data saved:
GET /api/v1/nlp/documents/{id}/results/


---

## **Step 5: Save the File**

Press **`Ctrl + S`** to save the file.

---

## **✅ What You Should See:**

Your README.md should now end with:

```markdown
... (your existing content)

---

## 🔗 Integration Guide for Member 2

### How to connect your NLP module to the backend:

**Step 1:** Call this to get pending documents:
... (the rest of the integration guide)