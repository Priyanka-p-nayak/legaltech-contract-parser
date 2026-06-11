# contracts/services/pdf_extractor.py

# WHY THIS FILE EXISTS:
# This is the first step of the entire pipeline.
# When a user uploads a PDF contract, THIS function runs first.
# It opens the PDF, reads every page, and returns all the text as a string.
# That text string then gets passed to the text cleaner (next step).

# ── IMPORTS ───────────────────────────────────────────────────────────────────

# fitz is PyMuPDF — the library that reads PDF files
import fitz

# logging lets us record events (success, errors) to a log file or console
# This is better than print() in production because logs can be turned on/off
import logging

# os helps us work with file paths and check if files exist
import os

# ── LOGGING SETUP ─────────────────────────────────────────────────────────────

# Create a logger for this specific file
# __name__ is a Python built-in that gives the current module's name
# This helps you know which file produced a log message
logger = logging.getLogger(__name__)

# ── MAIN FUNCTION ─────────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_path):
    """
    Extract all text from a PDF file.
    
    This function opens a PDF, reads every single page,
    combines all the text together, and returns it as one big string.
    
    Arguments:
        pdf_path (str): The full file path to the PDF on disk
                        Example: "media/contracts/contract_001.pdf"
    
    Returns:
        str: All text from the PDF combined into one string
             Returns an empty string "" if the PDF has no text or an error occurs
    
    Example usage:
        text = extract_text_from_pdf("media/contracts/contract.pdf")
        print(text[:500])  # print first 500 characters
    """
    
    # ── STEP 1: VALIDATE THE FILE PATH ────────────────────────────────────────
    
    # Check if the file actually exists before trying to open it
    # os.path.exists() returns True if the file is there, False if not
    if not os.path.exists(pdf_path):
        # Log the error so it appears in the server log
        logger.error(f"PDF file not found: {pdf_path}")
        # Return an empty string so the rest of the pipeline doesn't crash
        return ""
    
    # Check if the path points to a file (not a folder)
    if not os.path.isfile(pdf_path):
        logger.error(f"Path is not a file: {pdf_path}")
        return ""
    
    # ── STEP 2: OPEN AND READ THE PDF ─────────────────────────────────────────
    
    # We use a 'try-except' block to catch any errors that PyMuPDF might throw
    # For example: corrupted PDFs, password-protected PDFs, empty files
    try:
        # fitz.open() opens the PDF and returns a Document object
        # We immediately store it in pdf_document variable
        pdf_document = fitz.open(pdf_path)
        
        # Log that we successfully opened the file
        logger.info(f"Opened PDF: {pdf_path} — {len(pdf_document)} pages found")
        
        # ── STEP 3: COLLECT TEXT FROM ALL PAGES ───────────────────────────────
        
        # We will store each page's text in this list first
        # Then we join them all at the end with a newline between pages
        all_pages_text = []
        
        # Loop through every page in the document
        # enumerate() gives us both page_index (0, 1, 2...) and the page object
        for page_index, page in enumerate(pdf_document):
            
            # get_text() reads all the text from this single page
            # It returns a string — could be empty for image-only pages
            page_text = page.get_text()
            
            # Only add pages that actually have text content
            # strip() removes leading/trailing whitespace
            # If the result is empty after stripping, skip this page
            if page_text.strip():
                all_pages_text.append(page_text)
                logger.debug(f"Page {page_index + 1}: extracted {len(page_text)} characters")
            else:
                # Log pages that had no readable text (could be image-only pages)
                logger.warning(f"Page {page_index + 1}: no text found (possibly an image scan)")
        
        # ── STEP 4: COMBINE ALL PAGE TEXT ─────────────────────────────────────
        
        # Join all pages together with a double newline between them
        # "\n\n" creates a visible gap between pages in the combined text
        full_text = "\n\n".join(all_pages_text)
        
        # ── STEP 5: CLOSE THE PDF ─────────────────────────────────────────────
        
        # Always close the document to free memory and release the file
        pdf_document.close()
        
        # Log how much text was extracted in total
        logger.info(f"Extraction complete: {len(full_text)} characters extracted from {pdf_path}")
        
        # Return the complete text string
        return full_text
    
    # ── STEP 6: HANDLE ERRORS ─────────────────────────────────────────────────
    
    except fitz.FileDataError as e:
        # This happens when the PDF is corrupted or not a valid PDF
        logger.error(f"Corrupted or invalid PDF: {pdf_path} — Error: {e}")
        return ""
    
    except PermissionError as e:
        # This happens when the file is locked by another program
        logger.error(f"Permission denied for file: {pdf_path} — Error: {e}")
        return ""
    
    except Exception as e:
        # This catches any other unexpected error
        # We log it for debugging but don't crash the whole application
        logger.error(f"Unexpected error reading PDF {pdf_path} — Error: {e}")
        return ""


def get_pdf_metadata(pdf_path):
    """
    Extract basic metadata from the PDF (author, title, creation date).
    
    This is a bonus function — useful for displaying information about the contract.
    
    Arguments:
        pdf_path (str): Path to the PDF file
    
    Returns:
        dict: A dictionary with metadata fields
              Example: {"title": "Service Agreement", "author": "John Doe", "pages": 5}
    """
    
    # Default metadata in case the file can't be opened
    # We use empty strings so the calling code doesn't crash on missing keys
    metadata = {
        "title": "",
        "author": "",
        "subject": "",
        "creator": "",
        "pages": 0,
    }
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        return metadata
    
    try:
        pdf_document = fitz.open(pdf_path)
        
        # pdf_document.metadata returns a dict with PDF's built-in metadata
        # Not all PDFs have metadata — some fields may be empty strings
        raw_metadata = pdf_document.metadata
        
        # Update our metadata dict with whatever the PDF provides
        # We use .get() with a default of "" to avoid KeyError
        metadata["title"]   = raw_metadata.get("title", "")
        metadata["author"]  = raw_metadata.get("author", "")
        metadata["subject"] = raw_metadata.get("subject", "")
        metadata["creator"] = raw_metadata.get("creator", "")
        metadata["pages"]   = len(pdf_document)
        
        pdf_document.close()
    
    except Exception as e:
        logger.error(f"Could not read metadata from {pdf_path}: {e}")
    
    return metadata