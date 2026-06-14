# contracts/services/test_full_pipeline.py

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s — %(name)s — %(levelname)s — %(message)s'
)

# When testing outside Django, import directly (no dot prefix)
from pdf_extractor      import extract_text_from_pdf, get_pdf_metadata
from text_cleaner       import clean_contract_text, split_into_clauses
from entity_extractor   import extract_all_entities
from clause_categorizer import categorize_all_clauses, get_category_summary
from risk_detector      import scan_contract_for_risks

def test_full_pipeline(pdf_path):
    """Test the complete pipeline end to end."""

    print("\n" + "="*60)
    print("FULL PIPELINE TEST")
    print("="*60)

    # Step 1
    print("\n[Step 1] Extracting text...")
    raw_text = extract_text_from_pdf(pdf_path)
    print(f"  Extracted {len(raw_text)} characters")

    # Step 2
    print("\n[Step 2] Cleaning text...")
    clean_text = clean_contract_text(raw_text)
    print(f"  Cleaned to {len(clean_text)} characters")

    # Step 3
    print("\n[Step 3] Splitting into clauses...")
    clauses = split_into_clauses(clean_text)
    print(f"  Found {len(clauses)} clauses")

    # Step 4
    print("\n[Step 4] Extracting entities...")
    entities = extract_all_entities(clean_text)
    print(f"  Companies:  {entities['company_names']}")
    print(f"  Dates:      {entities['dates']}")
    print(f"  Jurisdiction: {entities['jurisdiction']}")
    print(f"  Duration:   {entities['contract_duration']}")

    # Step 5
    print("\n[Step 5] Categorizing clauses...")
    categorized = categorize_all_clauses(clauses)
    summary = get_category_summary(categorized)
    print(f"  Category summary: {summary}")

    # Step 6
    print("\n[Step 6] Detecting risks...")
    risk_report = scan_contract_for_risks(categorized)
    print(f"  Overall risk: {risk_report['overall_risk_level']}")
    print(f"  Total risks:  {risk_report['total_risks_found']}")
    print(f"  HIGH:   {risk_report['high_risk_count']}")
    print(f"  MEDIUM: {risk_report['medium_risk_count']}")
    print(f"  LOW:    {risk_report['low_risk_count']}")

    if risk_report['risky_clauses']:
        print("\n  RISKY CLAUSES:")
        for rc in risk_report['risky_clauses'][:3]:
            print(f"    Heading: {rc['heading']}")
            for risk in rc['risks_found']:
                print(f"      ⚠ {risk['risk_level']}: {risk['risk_type']}")

    print("\n" + "="*60)
    print("PIPELINE TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    test_full_pipeline("sample_contract.pdf")