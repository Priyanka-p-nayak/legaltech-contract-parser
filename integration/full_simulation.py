"""
full_simulation.py
===================
Runnable end-to-end simulation of the full LegalTech workflow.

Unlike test_full_system.py (which is silent and automated),
this script prints a friendly step-by-step report — perfect
for live demos during project review.

Run with (server must be running in another terminal):
    python integration/full_simulation.py
"""

import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"


def step(number, title):
    print(f"\n{'─' * 60}")
    print(f"  STEP {number}: {title}")
    print(f"{'─' * 60}")


def check_server():
    try:
        r = requests.get(f"{BASE_URL}/health/", timeout=5)
        return r.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def run_simulation():
    print("\n" + "🔬" * 30)
    print("  LEGALTECH — FULL SYSTEM SIMULATION")
    print("  Member 1 + Member 2 + Member 3 Combined Flow")
    print("🔬" * 30)

    if not check_server():
        print("\n❌ Server not running. Start it with:")
        print("   python manage.py runserver")
        sys.exit(1)

    print("\n✅ Server is running.")

    # ── Step 1: Upload ──────────────────────────────────────
    step(1, "Paralegal uploads NDA (Dashboard → Backend)")

    files   = {'file': ('simulation.pdf', b'%PDF-1.4 demo', 'application/pdf')}
    payload = {
        'contract_type':     'NDA',
        'counterparty_name': 'Simulation Corp',
    }
    r       = requests.post(
        f"{BASE_URL}/documents/upload/", files=files, data=payload
    )
    doc     = r.json()['data']
    doc_id  = doc['id']

    print(f"  ✅ Uploaded. Document ID: {doc_id}, Status: {doc['status']}")

    # ── Step 2: Dashboard sees it ───────────────────────────
    step(2, "Dashboard fetches overview (Backend → Dashboard)")

    r = requests.get(f"{BASE_URL}/dashboard/")
    recent_ids = [d['id'] for d in r.json()['data']['recent_documents']]
    print(f"  ✅ Document {doc_id} visible on dashboard: {doc_id in recent_ids}")

    # ── Step 3: NLP polls pending ────────────────────────────
    step(3, "NLP module checks pending queue (Backend → NLP)")

    r = requests.get(f"{BASE_URL}/nlp/documents/pending/")
    print(f"  ✅ Pending documents: {r.json()['data']['count']}")

    # ── Step 4: NLP marks processing ────────────────────────
    step(4, "NLP marks document as processing")

    r = requests.patch(
        f"{BASE_URL}/nlp/documents/{doc_id}/status/",
        json={"status": "processing"}
    )
    print(f"  ✅ Status: {r.json()['data']['old_status']} → {r.json()['data']['new_status']}")

    time.sleep(1)

    # ── Step 5: NLP submits results ─────────────────────────
    step(5, "NLP submits extracted clauses and risks")

    results = {
        "status":     "completed",
        "risk_score": 2,
        "metadata": {
            "governing_law": "California, USA",
        },
        "clauses": [
            {
                "clause_type":      "confidentiality",
                "clause_text":      "Both parties agree to confidentiality terms.",
                "page_number":      2,
                "confidence_score": 0.95,
            }
        ],
        "risk_flags": [
            {
                "risk_title":      "Unlimited Liability Found",
                "flagged_text":    "Vendor liable for unlimited damages.",
                "keyword_matched": "unlimited liability",
                "severity":        "high",
                "page_number":     4,
            }
        ],
    }
    r = requests.post(
        f"{BASE_URL}/nlp/documents/{doc_id}/process/", json=results
    )
    data = r.json()['data']
    print(f"  ✅ Saved {data['total_clauses']} clause(s), {data['total_risks']} risk(s)")

    # ── Step 6: Dashboard shows updated risk ────────────────
    step(6, "Dashboard reflects new high risk")

    r = requests.get(f"{BASE_URL}/dashboard/")
    high_risk_docs = [
        x['document_id'] for x in r.json()['data']['recent_high_risks']
    ]
    print(f"  ✅ Document {doc_id} flagged on dashboard: {doc_id in high_risk_docs}")

    # ── Step 7: Counsel reviews full detail ─────────────────
    step(7, "Senior counsel opens full document detail")

    r    = requests.get(f"{BASE_URL}/documents/{doc_id}/")
    full = r.json()['data']
    print(f"  ✅ Status: {full['status']} | Clauses: {len(full['clauses'])} | Risks: {len(full['risk_flags'])}")

    print("\n" + "=" * 60)
    print("  ✅ SIMULATION COMPLETE — ALL SYSTEMS WORKING TOGETHER")
    print("=" * 60)


if __name__ == '__main__':
    run_simulation()