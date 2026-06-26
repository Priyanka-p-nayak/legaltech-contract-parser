"""
mock_nlp.py
===========
Simulates Member 2's NLP module calling Member 1's APIs.

This script:
1. Gets pending documents from backend
2. Marks each as 'processing'
3. Simulates NLP extraction (fake clauses + risks)
4. Submits results to backend via API
5. Verifies results were saved

Run this script while Django server is running:
    python integration/mock_nlp.py

Requirements:
    pip install requests
"""

import requests
import json
import sys
import time

# ── Configuration ──────────────────────────────────────────
BASE_URL   = "http://127.0.0.1:8000/api/v1"
HEADERS    = {"Content-Type": "application/json"}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def print_section(title):
    """Print a section header for readability."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_response(response, label="Response"):
    """Print formatted API response."""
    print(f"\n{label}:")
    print(f"  Status Code : {response.status_code}")
    try:
        data = response.json()
        print(f"  Success     : {data.get('success')}")
        print(f"  Message     : {data.get('message')}")
    except Exception:
        print(f"  Body        : {response.text[:200]}")


def check_server():
    """Check if Django server is running."""
    try:
        response = requests.get(f"{BASE_URL}/health/", timeout=5)
        if response.status_code == 200:
            print("✅ Django server is running.")
            return True
        else:
            print("❌ Server returned unexpected status.")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server.")
        print("   Make sure Django is running:")
        print("   python manage.py runserver")
        return False


# ============================================================
# STEP 1: GET PENDING DOCUMENTS
# ============================================================

def get_pending_documents():
    """
    Call GET /api/v1/nlp/documents/pending/
    Returns list of documents waiting for NLP.
    """
    print_section("STEP 1: Get Pending Documents")

    response = requests.get(
        f"{BASE_URL}/nlp/documents/pending/",
        headers=HEADERS
    )

    print_response(response, "Pending Documents")

    if response.status_code == 200:
        data      = response.json()
        documents = data['data']['documents']
        count     = data['data']['count']

        print(f"\n  Found {count} pending document(s).")

        for doc in documents:
            print(f"  → ID: {doc['id']} | File: {doc['file_name']}")

        return documents

    print("  ❌ Failed to get pending documents.")
    return []


# ============================================================
# STEP 2: MARK AS PROCESSING
# ============================================================

def mark_as_processing(document_id):
    """
    Call PATCH /api/v1/nlp/documents/{id}/status/
    Marks document as 'processing' while NLP runs.
    """
    print_section(f"STEP 2: Mark Document {document_id} as Processing")

    response = requests.patch(
        f"{BASE_URL}/nlp/documents/{document_id}/status/",
        headers=HEADERS,
        json={"status": "processing"}
    )

    print_response(response, "Status Update")

    if response.status_code == 200:
        data = response.json()
        print(
            f"\n  Status: "
            f"{data['data']['old_status']} → "
            f"{data['data']['new_status']}"
        )
        return True

    print("  ❌ Failed to update status.")
    return False


# ============================================================
# STEP 3: SIMULATE NLP EXTRACTION
# ============================================================

def simulate_nlp_extraction(document_id):
    """
    Simulates what Member 2's NLP module would extract.
    Returns fake but realistic data.
    """
    print_section(f"STEP 3: Simulate NLP Extraction for Doc {document_id}")
    print("  Simulating PyMuPDF text extraction...")
    time.sleep(1)
    print("  Simulating spaCy NLP processing...")
    time.sleep(1)
    print("  ✅ NLP extraction complete.")

    # Fake NLP results — realistic contract data
    nlp_results = {
        "status":     "completed",
        "risk_score": 3,
        "metadata": {
            "counterparty_name":   "Acme Corporation Pvt Ltd",
            "governing_law":       "State of California, USA",
            "contract_start_date": "2024-01-01",
            "contract_end_date":   "2025-12-31",
        },
        "clauses": [
            {
                "clause_type":      "confidentiality",
                "clause_text": (
                    "Both parties agree to maintain strict "
                    "confidentiality of all proprietary information "
                    "and trade secrets shared during this agreement "
                    "for a period of five years from the date hereof."
                ),
                "page_number":      2,
                "confidence_score": 0.96,
            },
            {
                "clause_type":      "termination",
                "clause_text": (
                    "Either party may terminate this agreement "
                    "by providing thirty days written notice "
                    "to the other party via certified mail."
                ),
                "page_number":      5,
                "confidence_score": 0.91,
            },
            {
                "clause_type":      "governing_law",
                "clause_text": (
                    "This agreement shall be governed by and "
                    "construed in accordance with the laws of "
                    "the State of California."
                ),
                "page_number":      8,
                "confidence_score": 0.94,
            },
            {
                "clause_type":      "indemnification",
                "clause_text": (
                    "Each party shall indemnify and hold harmless "
                    "the other party from any claims, damages, "
                    "losses and expenses including attorney fees."
                ),
                "page_number":      6,
                "confidence_score": 0.88,
            },
        ],
        "risk_flags": [
            {
                "risk_title":      "Unlimited Liability Clause",
                "flagged_text": (
                    "The vendor shall be liable for unlimited "
                    "damages arising from any breach of this "
                    "agreement whatsoever."
                ),
                "keyword_matched": "unlimited liability",
                "severity":        "high",
                "page_number":     4,
                "explanation": (
                    "Unlimited liability clauses expose the company "
                    "to uncapped financial risk and must be reviewed "
                    "by senior counsel before signing."
                ),
            },
            {
                "risk_title":      "Indemnification Risk",
                "flagged_text": (
                    "Each party shall indemnify and hold harmless "
                    "the other from all claims without limitation."
                ),
                "keyword_matched": "indemnify",
                "severity":        "high",
                "page_number":     6,
                "explanation": (
                    "Broad indemnification without limitation "
                    "creates significant financial exposure."
                ),
            },
            {
                "risk_title":      "Exclusive Rights Clause",
                "flagged_text": (
                    "The client retains exclusive rights to all "
                    "work products, deliverables and intellectual "
                    "property created under this agreement."
                ),
                "keyword_matched": "exclusive",
                "severity":        "medium",
                "page_number":     7,
                "explanation": (
                    "Exclusive rights transfer may restrict "
                    "vendor's ability to use similar work "
                    "for other clients."
                ),
            },
        ],
    }

    print(f"\n  Extracted:")
    print(f"  → {len(nlp_results['clauses'])} clauses")
    print(f"  → {len(nlp_results['risk_flags'])} risk flags")
    print(f"  → Risk score: {nlp_results['risk_score']}")

    return nlp_results


# ============================================================
# STEP 4: SUBMIT NLP RESULTS TO BACKEND
# ============================================================

def submit_nlp_results(document_id, nlp_results):
    """
    Call POST /api/v1/nlp/documents/{id}/process/
    Sends all NLP results to backend in one call.
    """
    print_section(f"STEP 4: Submit NLP Results for Doc {document_id}")

    response = requests.post(
        f"{BASE_URL}/nlp/documents/{document_id}/process/",
        headers=HEADERS,
        json=nlp_results
    )

    print_response(response, "Submit Results")

    if response.status_code == 201:
        data = response.json()['data']
        print(f"\n  ✅ Results saved successfully!")
        print(f"  → Document ID    : {data['document_id']}")
        print(f"  → Status         : {data['status']}")
        print(f"  → Risk Score     : {data['risk_score']}")
        print(f"  → Clauses Saved  : {data['total_clauses']}")
        print(f"  → Risks Saved    : {data['total_risks']}")
        return True

    print("  ❌ Failed to submit results.")
    print(f"  Response: {response.text[:300]}")
    return False


# ============================================================
# STEP 5: VERIFY RESULTS
# ============================================================

def verify_results(document_id):
    """
    Call GET /api/v1/nlp/documents/{id}/results/
    Verifies all data was saved correctly.
    """
    print_section(f"STEP 5: Verify Results for Doc {document_id}")

    response = requests.get(
        f"{BASE_URL}/nlp/documents/{document_id}/results/",
        headers=HEADERS
    )

    print_response(response, "Verification")

    if response.status_code == 200:
        data = response.json()['data']

        print(f"\n  ✅ Verification successful!")
        print(f"\n  Document: {data['file_name']}")
        print(f"  Status  : {data['status']}")
        print(f"\n  Clauses ({data['clauses']['total']} total):")

        for clause_type, clauses in data['clauses']['by_type'].items():
            print(f"    → {clause_type}: {len(clauses)} clause(s)")

        print(f"\n  Risk Flags ({data['risk_flags']['total']} total):")
        by_severity = data['risk_flags']['by_severity']
        print(f"    → High   : {len(by_severity.get('high', []))}")
        print(f"    → Medium : {len(by_severity.get('medium', []))}")
        print(f"    → Low    : {len(by_severity.get('low', []))}")

        return True

    print("  ❌ Verification failed.")
    return False


# ============================================================
# STEP 6: CHECK DOCUMENT DETAIL
# ============================================================

def check_document_detail(document_id):
    """
    Call GET /api/v1/documents/{id}/
    Shows final document with all data nested.
    """
    print_section(f"STEP 6: Final Document Detail for Doc {document_id}")

    response = requests.get(
        f"{BASE_URL}/documents/{document_id}/",
        headers=HEADERS
    )

    if response.status_code == 200:
        data = response.json()['data']

        print(f"\n  ✅ Final document state:")
        print(f"  File Name        : {data['file_name']}")
        print(f"  Contract Type    : {data['contract_type']}")
        print(f"  Counterparty     : {data['counterparty_name']}")
        print(f"  Governing Law    : {data['governing_law']}")
        print(f"  Status           : {data['status']}")
        print(f"  Risk Score       : {data['risk_score']}")
        print(f"  Total Clauses    : {data['total_clauses']}")
        print(f"  Total Risks      : {data['total_risks']}")
        return True

    print("  ❌ Could not get document detail.")
    return False


# ============================================================
# MAIN: RUN FULL NLP SIMULATION
# ============================================================

def run_full_simulation():
    """
    Run the complete NLP integration simulation.
    Processes ALL pending documents.
    """
    print("\n" + "🔬" * 30)
    print("  LEGALTECH NLP INTEGRATION SIMULATION")
    print("  Simulating Member 2 NLP Module Calls")
    print("🔬" * 30)

    # Check server is running
    if not check_server():
        sys.exit(1)

    # Step 1: Get pending documents
    documents = get_pending_documents()

    if not documents:
        print("\n⚠️  No pending documents found.")
        print("   Upload a PDF first via:")
        print("   POST /api/v1/documents/upload/")
        print("\n   Then run this script again.")
        sys.exit(0)

    # Process each pending document
    success_count = 0

    for doc in documents:
        doc_id    = doc['id']
        file_name = doc['file_name']

        print(f"\n\n{'─' * 60}")
        print(f"  Processing: {file_name} (ID: {doc_id})")
        print(f"{'─' * 60}")

        # Step 2: Mark as processing
        if not mark_as_processing(doc_id):
            continue

        # Step 3: Simulate NLP extraction
        nlp_results = simulate_nlp_extraction(doc_id)

        # Step 4: Submit results
        if not submit_nlp_results(doc_id, nlp_results):
            continue

        # Step 5: Verify saved data
        if not verify_results(doc_id):
            continue

        # Step 6: Show final state
        check_document_detail(doc_id)

        success_count += 1

    # Final summary
    print_section("SIMULATION COMPLETE")
    print(f"\n  Documents Processed : {success_count}/{len(documents)}")

    if success_count == len(documents):
        print("  Status             : ✅ ALL SUCCESSFUL")
        print("\n  Your backend APIs are working correctly.")
        print("  Member 2 can now connect their NLP module.")
    else:
        print("  Status             : ⚠️  SOME FAILED")
        print("  Check error messages above.")


# ── Entry point ────────────────────────────────────────────
if __name__ == '__main__':
    run_full_simulation()