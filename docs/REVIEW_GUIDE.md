# Reviewer's Tour — LegalTech Backend

**For:** Project reviewer / mentor  
**Time required:** 15–20 minutes for full walkthrough  
**Built by:** Member 1 — Backend, Database & APIs

This document is a guided tour of the code, in the exact  
order that makes the most logical sense to a reviewer.

---

## Quick Context (Read Before Opening Any Code)

This is a **3-person internship project**. I (Member 1) am  
responsible for the entire backend layer:

- **Member 1** → Django Backend + PostgreSQL + REST APIs (THIS REPO)
- **Member 2** → PDF text extraction (PyMuPDF) + NLP (spaCy)
- **Member 3** → Dashboard UI

Everything in this repo is **my work only**. Member 2 and  
Member 3 call my APIs from their separate codebases.

---

## Step 1 — Start at the README (2 minutes)

**Open:** `README.md`

**What to look for:**
- Badges showing test count, Docker readiness, backend tech
- Architecture diagram showing all 3 members' parts
- "My Role — Member 1" section listing everything I built
- Quick Start section (one command to run everything)

---

## Step 2 — Database Models (3 minutes)

**Open:** `contracts/models.py`

**Talk through:**
1. **`DocumentManager`** at the top — custom query methods  
   so `Document.objects.pending()` reads like English
2. **`Document` model** — the central record. Explain why  
   `file_name` is separate from `file` (storage vs display).  
   Explain why `risk_score` exists separately from counting  
   `RiskFlag` rows (NLP module's weighted score vs raw count).
3. **`ExtractedClause`** — child of Document via ForeignKey  
   with `related_name='clauses'` so we write  
   `document.clauses.all()` everywhere
4. **`RiskFlag`** — another child, `is_resolved` is a boolean  
   not a status because there are only ever 2 states

**If reviewer asks "why PostgreSQL not SQLite?":**  
→ See the Design Decisions section in `docs/DATABASE_MODELS.md`

---

## Step 3 — API Endpoints (3 minutes)

**Open:** `contracts/urls.py`

**Talk through the 3 groups:**
1. **Utility** — health check and stats
2. **Document-facing** — what Member 3's dashboard calls
3. **NLP-facing** — what Member 2's NLP module calls

**Key point:** "I deliberately separated NLP endpoints into  
`nlp_views.py` so Member 2 only ever needs to read ONE file  
to understand every endpoint they can call."

Then open: `contracts/views.py` briefly — show one complete  
view (`DashboardOverviewView` is good) to demonstrate the  
consistent `api_response()` helper pattern.

---

## Step 4 — Error Handling (2 minutes)

**Open:** `contracts/exceptions.py`

**Show 2–3 exception classes. Key points:**
- Every exception bundles HTTP status code + error_code + message
- 400 for bad input, 404 for missing resources, 409 for conflicts
- 413 for oversized files (not 400 — semantically different)

Then open: `legaltech_project/error_handlers.py`

**Show `custom_exception_handler`** — "this single function  
catches EVERY exception in the whole API and guarantees  
the response always has the same JSON shape."

---

## Step 5 — NLP Integration (2 minutes)

**Open:** `contracts/nlp_views.py`

**Show `NLPProcessResultView.post`** — the main integration  
endpoint. Key points:
- `transaction.atomic()` means if ANYTHING fails,  
  NOTHING is saved — no partial states in the database
- Validates status value before any DB writes
- 100-item bulk limit on clauses and risks

**Say:** "I built a mock simulation script so I could prove  
this flow works without needing Member 2's actual code.  
Let me show you."

Open a second terminal and run:
```bash
python integration/full_simulation.py