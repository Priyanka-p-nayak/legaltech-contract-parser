# contracts/services/test_entity_extractor.py

import logging
logging.basicConfig(level=logging.INFO)

from entity_extractor import extract_all_entities

def test_entity_extraction():

    sample_contract = """
    SERVICE AGREEMENT

    This Service Agreement ("Agreement") is entered into as of January 1, 2024,
    between Tata Consultancy Services Limited, a company incorporated under the
    laws of India, with its registered office at Mumbai, Maharashtra
    (hereinafter referred to as "Service Provider"),

    and Reliance Industries Limited, having its principal place of business
    at New Delhi, India (hereinafter referred to as "Client").

    TERM:
    This Agreement shall be in force for a period of two (2) years commencing
    from January 1, 2024 and ending on December 31, 2025.

    GOVERNING LAW:
    This Agreement shall be governed by the laws of India.
    Any disputes shall be subject to the exclusive jurisdiction of
    the courts of Mumbai, Maharashtra.
    """

    print("=" * 60)
    print("RUNNING ENTITY EXTRACTION TEST")
    print("=" * 60)

    results = extract_all_entities(sample_contract)

    print("\nCOMPANY NAMES:")
    for name in results["company_names"]:
        print(f"  - {name}")

    print("\nDATES:")
    for date in results["dates"]:
        print(f"  - {date}")

    print(f"\nJURISDICTION:  {results['jurisdiction']}")
    print(f"DURATION:      {results['contract_duration']}")
    print(f"SUCCESS:       {results['extraction_successful']}")


if __name__ == "__main__":
    test_entity_extraction()