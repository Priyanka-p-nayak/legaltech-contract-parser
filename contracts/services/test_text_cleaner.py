# contracts/services/test_text_cleaner.py

import logging
logging.basicConfig(level=logging.DEBUG)

from text_cleaner import clean_contract_text, split_into_clauses

def test_cleaning():
    
    # Sample messy text simulating raw PDF output
    messy_text = """CONFIDENTIAL
    
    This  Agreement   is  entered\ninto between  ACME Corporation
    and  Beta  Ltd.   on  January  15,  2024.
    
    Page 1 of 5
    
    1. DEFINITIONS
    In this agreement, "Party A" means ACME Corporation.
    
    CONFIDENTIAL
    
    2. PAYMENT TERMS
    The client shall pay within thirty (30) days of invoice.
    Failure to pay shall  result   in  a penalty\nof 2% per month.
    
    Page 2 of 5
    
    3. INDEMNIFICATION
    Party A shall indemnify and hold harmless Party B from any claims.
    """
    
    print("=" * 60)
    print("ORIGINAL TEXT:")
    print("=" * 60)
    print(messy_text)
    
    cleaned = clean_contract_text(messy_text)
    
    print("\n" + "=" * 60)
    print("CLEANED TEXT:")
    print("=" * 60)
    print(cleaned)
    
    print("\n" + "=" * 60)
    print("SPLIT INTO CLAUSES:")
    print("=" * 60)
    
    clauses = split_into_clauses(cleaned)
    for i, clause in enumerate(clauses):
        print(f"\nClause {i+1}:")
        print(f"  Heading: {clause['heading']}")
        print(f"  Content: {clause['content'][:100]}...")

if __name__ == "__main__":
    test_cleaning()