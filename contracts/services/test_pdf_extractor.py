# contracts/services/test_pdf_extractor.py

# This tests our pdf_extractor.py
# Run it in the terminal to see if extraction works

import logging

# Set up logging so we can see the log messages
logging.basicConfig(level=logging.DEBUG)

# Import our function from the same folder
from pdf_extractor import extract_text_from_pdf, get_pdf_metadata

def test_extraction():
    """Test the PDF extractor with a sample file."""
    
    # ── TEST 1: Extract text ───────────────────────────────────────────────────
    print("=" * 50)
    print("TEST 1: Text Extraction")
    print("=" * 50)
    
    extracted_text = extract_text_from_pdf("sample_contract.pdf")
    
    if extracted_text:
        print(f"SUCCESS — Extracted {len(extracted_text)} characters")
        print("\nFirst 300 characters:")
        print(extracted_text[:300])
    else:
        print("FAILED — No text extracted")
    
    # ── TEST 2: Metadata ───────────────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("TEST 2: PDF Metadata")
    print("=" * 50)
    
    metadata = get_pdf_metadata("sample_contract.pdf")
    print("Metadata found:")
    for key, value in metadata.items():
        print(f"  {key}: {value}")
    
    # ── TEST 3: Non-existent file ──────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("TEST 3: File Not Found (should return empty string)")
    print("=" * 50)
    
    result = extract_text_from_pdf("does_not_exist.pdf")
    
    if result == "":
        print("SUCCESS — Empty string returned for missing file")
    else:
        print("FAILED — Should have returned empty string")


if __name__ == "__main__":
    test_extraction()