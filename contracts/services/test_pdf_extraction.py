# test_pdf_extraction.py

from contracts.services.pdf_extractor import extract_text_from_pdf

# Test with a real PDF file
# Replace with actual path to a PDF in your media/ folder
pdf_path = "media/contracts/your_test_contract.pdf"

print("Testing PDF extraction...")
result = extract_text_from_pdf(pdf_path)

if result["success"]:
    print(f"✓ Extracted {len(result['text'])} characters")
    print(f"✓ Pages: {result['metadata']['pages']}")
    print(f"\nFirst 200 chars:\n{result['text'][:200]}")
else:
    print(f"✗ Error: {result['error']}")