# contracts/services/test_clause_categorizer.py

import logging
logging.basicConfig(level=logging.INFO)

from clause_categorizer import categorize_clause, categorize_all_clauses, get_category_summary

def test_categorization():

    # Test individual clauses
    test_clauses = [
        {
            "text": "Party A shall indemnify and hold harmless Party B from any third party claims, losses, damages, and attorney fees arising from Party A's negligence.",
            "expected": "INDEMNIFICATION"
        },
        {
            "text": "Either party may terminate this agreement upon thirty (30) days written notice. Immediate termination is permitted for material breach.",
            "expected": "TERMINATION"
        },
        {
            "text": "The Client shall pay all invoices within 30 days. Late payment will attract an interest rate of 2% per month.",
            "expected": "PAYMENT_TERMS"
        },
        {
            "text": "This Agreement shall be governed by the laws of India. All disputes shall be subject to the jurisdiction of courts in Mumbai.",
            "expected": "GOVERNING_LAW"
        },
        {
            "text": "The Service Provider shall have exclusive rights to provide these services. The Client shall not engage any other supplier during the term.",
            "expected": "EXCLUSIVITY"
        },
    ]

    print("=" * 60)
    print("INDIVIDUAL CLAUSE CATEGORIZATION TEST")
    print("=" * 60)

    for i, test in enumerate(test_clauses):
        result = categorize_clause(test["text"])
        status = "✓ PASS" if result["category"] == test["expected"] else "✗ FAIL"

        print(f"\nTest {i+1}: {status}")
        print(f"  Expected : {test['expected']}")
        print(f"  Got      : {result['category']}")
        print(f"  Score    : {result['score']}")
        print(f"  Keywords : {result['matched_keywords'][:3]}")


if __name__ == "__main__":
    test_categorization()