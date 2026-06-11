# contracts/services/test_connection.py

# WHY THIS FILE EXISTS:
# This is a simple test file to verify your environment works.
# You will delete it before the final submission.

# Import Django's ORM to check DB connection
import django
import os

# This line tells Python where Django's settings are
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legaltech.settings')

def test_python_environment():
    """
    This function checks if all required packages are installed.
    
    We import each library and print a success message.
    If any import fails, Python will show an error and you know what to install.
    """
    
    # Test PyMuPDF (for PDF reading)
    import fitz
    print("✓ PyMuPDF (fitz) is installed")
    
    # Test spaCy (for NLP)
    import spacy
    print("✓ spaCy is installed")
    
    # Test spaCy English model
    nlp = spacy.load("en_core_web_sm")
    print("✓ spaCy English model loaded")
    
    # Test Django
    print("✓ Django is installed")
    
    print("\n All packages are working correctly!")
    print("You are ready to start coding.")

# This block runs only when you run this file directly
# It does NOT run when another file imports this module
if __name__ == "__main__":
    test_python_environment()