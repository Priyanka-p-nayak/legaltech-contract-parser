# contracts/services/learn_pymupdf.py

# WHY THIS FILE EXISTS:
# This is a LEARNING file. We practice using PyMuPDF here.
# Once we understand it, we write the real code in pdf_extractor.py

# fitz is the actual name of the PyMuPDF library
# Even though we installed it as 'pymupdf', we import it as 'fitz'
import fitz  # pip install pymupdf


def explore_pdf(pdf_path):
    """
    This function demonstrates how PyMuPDF works.
    
    Arguments:
        pdf_path (str): The full file path to the PDF file
        
    Returns:
        None (just prints information)
    """
    
    # Step 1: Open the PDF file
    # fitz.open() returns a Document object — think of it as the whole book
    pdf_document = fitz.open(pdf_path)
    
    # Step 2: Check how many pages the PDF has
    # len() on a fitz document gives the page count
    total_pages = len(pdf_document)
    print(f"PDF has {total_pages} pages")
    
    # Step 3: Loop through each page
    # enumerate gives us both the index (0, 1, 2...) and the page object
    for page_number, page in enumerate(pdf_document):
        
        print(f"\n--- Page {page_number + 1} ---")
        
        # Step 4: Extract text from this page
        # get_text() returns all text as one big string
        page_text = page.get_text()
        
        # Step 5: Show the first 200 characters as a preview
        # This avoids printing thousands of characters to the screen
        print(page_text[:200])
        
        # Show how many characters were extracted from this page
        print(f"(Total characters on this page: {len(page_text)})")
    
    # Step 6: ALWAYS close the PDF when done
    # This frees up memory and releases the file lock
    pdf_document.close()
    print("\nPDF closed successfully.")


# Run this when the file is executed directly
if __name__ == "__main__":
    # Change this path to wherever your sample PDF is
    pdf_path = "sample_contract.pdf"
    explore_pdf(pdf_path)