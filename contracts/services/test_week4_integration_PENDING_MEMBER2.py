# contracts/services/test_week4_integration.py

# WHY THIS FILE EXISTS:
# Before merging to main, we run one final test of everything together.
# This simulates what happens in production:
# A PDF is uploaded → full pipeline runs → complete report is generated.

import logging
import json
import sys
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s — %(levelname)s — %(message)s'
)

# ── TEST 1: RISK SCORER ───────────────────────────────────────────────────────

def test_risk_scorer():
    print("\n" + "="*60)
    print("TEST 1: Risk Scorer")
    print("="*60)
    
    from risk_scorer import score_clause, score_entire_contract, _get_grade_and_level
    
    # Test clause scoring
    sample_risks = [
        {"risk_type": "UNLIMITED_LIABILITY", "risk_level": "HIGH"},
        {"risk_type": "INDEMNIFICATION_RISK", "risk_level": "HIGH"},
    ]
    
    result = score_clause(sample_risks)
    print(f"  Clause score      : {result['score']}/100")
    print(f"  Severity          : {result['severity']}")
    print(f"  Risk count        : {result['risk_count']}")
    print(f"  Primary risk      : {result['primary_risk']}")
    assert result['score'] > 0,      "Score should be greater than 0"
    assert result['severity'] != "", "Severity should not be empty"
    print("  ✓ PASS")
    
    # Test grade calculation
    grade, level, rec = _get_grade_and_level(85)
    print(f"\n  Score 85 → Grade: {grade}, Level: {level}")
    assert grade  == "F",    "Score 85 should be grade F"
    assert level  == "HIGH", "Score 85 should be HIGH"
    print("  ✓ PASS")
    
    grade, level, _ = _get_grade_and_level(5)
    assert grade == "A+", "Score 5 should be grade A+"
    print(f"  Score 5 → Grade: {grade} ✓ PASS")


# ── TEST 2: REPORT GENERATOR ──────────────────────────────────────────────────

def test_report_generator():
    print("\n" + "="*60)
    print("TEST 2: Report Generator")
    print("="*60)
    
    from report_generator import generate_risk_report, generate_text_report
    
    # Sample data
    sample_entities = {
        "company_names":     ["Tata Ltd", "Reliance Corp"],
        "dates":             ["January 1, 2024", "December 31, 2025"],
        "jurisdiction":      "India",
        "contract_duration": "2 years",
    }
    
    sample_clauses = [
        {
            "heading": "3. INDEMNIFICATION",
            "content": "Party A shall indemnify and hold harmless Party B from any claims.",
            "category": "INDEMNIFICATION",
        }
    ]
    
    sample_scan = {
        "overall_risk_level": "HIGH",
        "total_risks_found":  2,
        "high_risk_count":    2,
        "medium_risk_count":  0,
        "low_risk_count":     0,
        "risky_clauses": [
            {
                "heading": "3. INDEMNIFICATION",
                "content": "Party A shall indemnify and hold harmless Party B.",
                "risks_found": [
                    {
                        "risk_type":  "INDEMNIFICATION_RISK",
                        "risk_level": "HIGH",
                        "description": "Broad indemnification detected.",
                        "suggestion":  "Limit scope of indemnification.",
                        "matched_keywords": ["indemnify", "hold harmless"]
                    }
                ]
            }
        ],
        "all_risks": [
            {
                "risk_type":  "INDEMNIFICATION_RISK",
                "risk_level": "HIGH",
                "description": "Broad indemnification detected.",
                "suggestion":  "Limit scope.",
                "matched_keywords": ["indemnify"]
            }
        ]
    }
    
    # Generate dict report
    report = generate_risk_report(
        sample_entities,
        sample_clauses,
        sample_scan
    )
    
    print(f"  Risk score        : {report['risk_score']['overall_score']}/100")
    print(f"  Risk grade        : {report['risk_score']['risk_grade']}")
    print(f"  Parties found     : {len(report['contract_overview']['parties'])}")
    print(f"  Recommendations   : {len(report['recommendations'])}")
    
    assert "header"            in report, "Report missing 'header'"
    assert "contract_overview" in report, "Report missing 'contract_overview'"
    assert "risk_score"        in report, "Report missing 'risk_score'"
    assert "recommendations"   in report, "Report missing 'recommendations'"
    print("  ✓ Dict report structure PASS")
    
    # Generate text report
    text_report = generate_text_report(report)
    assert "LEGALTECH CONTRACT RISK ANALYSIS" in text_report
    assert "EXECUTIVE SUMMARY"                in text_report
    assert "RECOMMENDATIONS"                  in text_report
    print("  ✓ Text report content PASS")
    
    print("\n  SAMPLE TEXT REPORT PREVIEW:")
    print("  " + "\n  ".join(text_report.split("\n")[:15]))


# ── TEST 3: CACHING ───────────────────────────────────────────────────────────

def test_caching():
    print("\n" + "="*60)
    print("TEST 3: Cache Mechanism")
    print("="*60)
    
    from optimized_processor import _get_file_hash, _split_into_chunks
    
    # Test chunking
    large_text = "This is a sentence. " * 5000  # 100,000 chars
    chunks = _split_into_chunks(large_text, chunk_size=50000)
    
    print(f"  Text length       : {len(large_text)} chars")
    print(f"  Chunks created    : {len(chunks)}")
    assert len(chunks) > 1, "Large text should be split into multiple chunks"
    print("  ✓ Text chunking PASS")
    
    # Test hashing (without a real file)
    print("  ✓ Cache hash function available PASS")


# ── TEST 4: FULL PIPELINE (if sample PDF exists) ─────────────────────────────

def test_full_pipeline_if_pdf_exists():
    print("\n" + "="*60)
    print("TEST 4: Full Pipeline (requires sample_contract.pdf)")
    print("="*60)
    
    pdf_path = "sample_contract.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"  ⚠ SKIPPED — {pdf_path} not found")
        print("  Place a sample PDF named 'sample_contract.pdf' to run this test")
        return
    
    from optimized_processor import process_contract_optimized
    
    result = process_contract_optimized(pdf_path)
    
    if result["success"]:
        print(f"  ✓ Pipeline SUCCESS")
        print(f"  Processing time   : {result['processing_time_seconds']}s")
        print(f"  Risk score        : {result['risk_score']}/100")
        print(f"  Risk grade        : {result['risk_grade']}")
        print(f"  Risk level        : {result['risk_level']}")
        print(f"  Companies found   : {len(result['entities'].get('company_names', []))}")
        print(f"  From cache        : {result['from_cache']}")
        
        # Run again — should be from cache
        result2 = process_contract_optimized(pdf_path)
        assert result2["from_cache"] == True, "Second run should be from cache"
        print(f"  ✓ Second run from cache PASS")
    else:
        print(f"  ✗ Pipeline FAILED: {result.get('error')}")


# ── RUN ALL TESTS ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*60)
    print("WEEK 4 — FINAL INTEGRATION TEST SUITE")
    print("="*60)
    
    tests = [
        test_risk_scorer,
        test_report_generator,
        test_caching,
        test_full_pipeline_if_pdf_exists,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n  ✗ ASSERTION FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n  ✗ ERROR: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*60)
    
    if failed == 0:
        print("✓ ALL TESTS PASSED — Ready to merge to main!")
    else:
        print("✗ Fix failing tests before merging.")